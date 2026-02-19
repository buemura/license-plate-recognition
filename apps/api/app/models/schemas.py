from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.recognition import RecognitionStatus


class RecognitionRequestCreate(BaseModel):
    pass


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected plate region."""

    x: int
    y: int
    width: int
    height: int


class RecognitionRequestResponse(BaseModel):
    id: UUID
    image_url: str
    plate_number: str | None
    status: RecognitionStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    # New optional fields for enhanced recognition (backward compatible)
    confidence_score: float | None = None
    detection_confidence: float | None = None
    ocr_confidence: float | None = None
    needs_review: bool = False
    bounding_box: BoundingBox | None = None
    plate_region: str | None = None

    model_config = {"from_attributes": True}


class RecognitionRequestSubmitResponse(BaseModel):
    request_id: UUID
    status: RecognitionStatus
    created_at: datetime


class RecognitionRequestListResponse(BaseModel):
    items: list[RecognitionRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
