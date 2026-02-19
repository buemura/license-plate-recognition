from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "License Plate Recognition API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/plate_recognition"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_type: str = "local"  # local, s3, supabase
    upload_dir: str = "uploads"

    # AWS S3 (optional)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_bucket_name: str | None = None
    aws_region: str = "us-east-1"

    # Supabase (optional)
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_bucket: str | None = None

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Recognition - Detection
    use_plate_detection: bool = True
    plate_detection_model: str = "yolov8n.pt"
    plate_detection_confidence: float = 0.5

    # Recognition - OCR
    ocr_min_confidence: float = 0.3
    ocr_gpu: bool = False

    # Recognition - Confidence thresholds
    needs_review_threshold: float = 0.6
    auto_accept_threshold: float = 0.85

    # Recognition - Retry settings
    enable_enhanced_retry: bool = True
    max_processing_attempts: int = 3

    # Recognition - Validation
    default_plate_region: str = "BR"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
