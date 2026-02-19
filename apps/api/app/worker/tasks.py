"""Celery tasks for license plate recognition."""

import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RecognitionRequest, RecognitionStatus
from app.services.recognition import (
    RecognitionConfig,
    RecognitionService,
)
from app.shared.config import get_settings
from app.worker.celery_app import celery_app

# Synchronous database setup for Celery worker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

settings = get_settings()

# Convert async URL to sync URL for Celery
sync_database_url = settings.database_url.replace(
    "postgresql+asyncpg://", "postgresql://"
)
sync_engine = create_engine(sync_database_url)
SyncSession = sessionmaker(bind=sync_engine)


def _create_recognition_service() -> RecognitionService:
    """Create recognition service with settings from config."""
    config = RecognitionConfig(
        use_plate_detection=settings.use_plate_detection,
        plate_detection_model=settings.plate_detection_model,
        detection_confidence=settings.plate_detection_confidence,
        min_ocr_confidence=settings.ocr_min_confidence,
        ocr_gpu=settings.ocr_gpu,
        default_region=settings.default_plate_region,
        needs_review_threshold=settings.needs_review_threshold,
        auto_accept_threshold=settings.auto_accept_threshold,
        enable_enhanced_retry=settings.enable_enhanced_retry,
        max_processing_attempts=settings.max_processing_attempts,
    )
    return RecognitionService(config=config)


@celery_app.task(bind=True, max_retries=3)
def process_plate_recognition(self, request_id: str):
    """Process license plate recognition asynchronously.

    Uses the enhanced recognition pipeline with:
    - Plate detection (YOLOv8)
    - Advanced preprocessing
    - Context-based validation
    - Confidence scoring
    """
    db: Session = SyncSession()

    try:
        # Get the recognition request
        result = db.execute(
            select(RecognitionRequest).where(
                RecognitionRequest.id == uuid.UUID(request_id)
            )
        )
        recognition_request = result.scalar_one_or_none()

        if not recognition_request:
            raise ValueError(f"Recognition request {request_id} not found")

        # Mark as PENDING (processing started)
        recognition_request.status = RecognitionStatus.PENDING
        db.commit()

        # Get the image path from URL
        image_url = recognition_request.image_url
        # Convert URL to file path (e.g., /uploads/file.jpg -> uploads/file.jpg)
        image_filename = image_url.lstrip("/").replace("uploads/", "")
        image_path = Path(settings.upload_dir) / image_filename

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Process the image using enhanced pipeline
        recognition_service = _create_recognition_service()
        recognition_result = recognition_service.process_image(image_path)

        # Update the request with full recognition results
        # Convert numpy types to native Python types for database storage
        recognition_request.plate_number = recognition_result.plate_number
        recognition_request.confidence_score = float(recognition_result.confidence_score)
        recognition_request.detection_confidence = float(recognition_result.detection_confidence)
        recognition_request.ocr_confidence = float(recognition_result.ocr_confidence)
        recognition_request.needs_review = bool(recognition_result.needs_review)
        recognition_request.bounding_box = recognition_result.bounding_box
        recognition_request.plate_region = recognition_result.plate_region

        # Determine status based on result
        if recognition_result.plate_number:
            if recognition_result.needs_review:
                recognition_request.status = RecognitionStatus.NEEDS_REVIEW
            else:
                recognition_request.status = RecognitionStatus.COMPLETED
            recognition_request.error_message = None
        else:
            recognition_request.status = RecognitionStatus.FAILED
            recognition_request.error_message = "No plate detected"

        db.commit()

        logger.info(
            f"Recognition completed for {request_id}: "
            f"plate={recognition_result.plate_number}, "
            f"confidence={recognition_result.confidence_score:.2f}, "
            f"needs_review={recognition_result.needs_review}"
        )

        # Convert numpy types to native Python types for JSON serialization
        return {
            "request_id": request_id,
            "plate_number": recognition_result.plate_number,
            "status": recognition_request.status.value,
            "confidence_score": float(recognition_result.confidence_score),
            "detection_confidence": float(recognition_result.detection_confidence),
            "ocr_confidence": float(recognition_result.ocr_confidence),
            "needs_review": bool(recognition_result.needs_review),
            "plate_region": recognition_result.plate_region,
        }

    except Exception as e:
        logger.error(f"Recognition failed for {request_id}: {e}")

        # Update status to FAILED - rollback first to clear any broken transaction
        try:
            db.rollback()
            if "recognition_request" in locals() and recognition_request:
                recognition_request.status = RecognitionStatus.FAILED
                recognition_request.error_message = str(e)
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update status for {request_id}: {db_err}")
            db.rollback()

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5 * (self.request.retries + 1))

        return {
            "request_id": request_id,
            "plate_number": None,
            "status": "FAILED",
            "error": str(e),
        }

    finally:
        db.close()
