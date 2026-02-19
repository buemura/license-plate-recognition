import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class RecognitionStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RecognitionRequest(Base):
    __tablename__ = "recognition_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    plate_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[RecognitionStatus] = mapped_column(
        Enum(RecognitionStatus), default=RecognitionStatus.NOT_STARTED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Recognition confidence fields
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    detection_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Review flag
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Plate detection metadata
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    plate_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
