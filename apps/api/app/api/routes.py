import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_db
from app.models import (
    RecognitionRequest,
    RecognitionStatus,
    RecognitionRequestListResponse,
    RecognitionRequestResponse,
    RecognitionRequestSubmitResponse,
)
from app.services.storage import get_storage_service, StorageService
from app.worker.tasks import process_plate_recognition

router = APIRouter(prefix="/api/v1/recognition", tags=["recognition"])


@router.post("", response_model=RecognitionRequestSubmitResponse)
async def submit_recognition_request(
    file: Annotated[UploadFile, File(description="License plate image")],
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    request_id = uuid.uuid4()
    file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{request_id}.{file_extension}"

    file_content = await file.read()
    image_url = await storage.save(filename, file_content)

    recognition_request = RecognitionRequest(
        id=request_id,
        image_url=image_url,
        status=RecognitionStatus.NOT_STARTED,
    )

    db.add(recognition_request)
    await db.commit()
    await db.refresh(recognition_request)

    process_plate_recognition.delay(str(request_id))

    return RecognitionRequestSubmitResponse(
        request_id=recognition_request.id,
        status=recognition_request.status,
        created_at=recognition_request.created_at,
    )


@router.post("/{request_id}/reprocess", response_model=RecognitionRequestSubmitResponse)
async def reprocess_recognition_request(
    request_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(RecognitionRequest).where(RecognitionRequest.id == request_id)
    )
    recognition_request = result.scalar_one_or_none()

    if not recognition_request:
        raise HTTPException(status_code=404, detail="Recognition request not found")

    if recognition_request.status not in (
        RecognitionStatus.FAILED,
        RecognitionStatus.NEEDS_REVIEW,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only FAILED or NEEDS_REVIEW requests can be reprocessed",
        )

    recognition_request.status = RecognitionStatus.NOT_STARTED
    recognition_request.plate_number = None
    recognition_request.error_message = None
    recognition_request.confidence_score = None
    recognition_request.detection_confidence = None
    recognition_request.ocr_confidence = None
    recognition_request.needs_review = False
    recognition_request.bounding_box = None
    recognition_request.plate_region = None

    await db.commit()
    await db.refresh(recognition_request)

    process_plate_recognition.delay(str(request_id))

    return RecognitionRequestSubmitResponse(
        request_id=recognition_request.id,
        status=recognition_request.status,
        created_at=recognition_request.created_at,
    )


@router.get("/{request_id}", response_model=RecognitionRequestResponse)
async def get_recognition_request(
    request_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(RecognitionRequest).where(RecognitionRequest.id == request_id)
    )
    recognition_request = result.scalar_one_or_none()

    if not recognition_request:
        raise HTTPException(status_code=404, detail="Recognition request not found")

    return recognition_request


@router.get("", response_model=RecognitionRequestListResponse)
async def list_recognition_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count(RecognitionRequest.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(RecognitionRequest)
        .order_by(RecognitionRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return RecognitionRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
