"""License plate recognition service - main orchestrator."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import re

import cv2
import numpy as np

from app.services.detection import (
    BoundingBox,
    DetectionResult,
    PlateDetector,
    YOLOPlateDetector,
)
from app.services.detection.yolo_detector import FallbackDetector
from app.services.ocr import EasyOCREngine, OCREngine, OCRResult
from app.services.preprocessing import PreprocessingPipeline
from app.services.preprocessing.pipeline import PreprocessingConfig
from app.services.validation import PlateFormatRegistry, PlateValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class RecognitionConfig:
    """Configuration for recognition pipeline."""

    # Detection
    use_plate_detection: bool = True
    plate_detection_model: str = "yolov8n.pt"
    detection_confidence: float = 0.5
    detection_padding: int = 10

    # OCR
    ocr_languages: list[str] = field(default_factory=lambda: ["en"])
    ocr_gpu: bool = False
    min_ocr_confidence: float = 0.3

    # Preprocessing
    preprocessing_config: PreprocessingConfig | None = None

    # Validation
    default_region: str = "BR"

    # Confidence thresholds
    needs_review_threshold: float = 0.6
    auto_accept_threshold: float = 0.85

    # Retry settings
    enable_enhanced_retry: bool = True
    max_processing_attempts: int = 3


@dataclass
class RecognitionResult:
    """Full result from recognition pipeline."""

    plate_number: str | None
    confidence_score: float
    detection_confidence: float
    ocr_confidence: float
    bounding_box: dict | None
    plate_region: str | None
    needs_review: bool
    processing_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "plate_number": self.plate_number,
            "confidence_score": self.confidence_score,
            "detection_confidence": self.detection_confidence,
            "ocr_confidence": self.ocr_confidence,
            "bounding_box": self.bounding_box,
            "plate_region": self.plate_region,
            "needs_review": self.needs_review,
            "processing_metadata": self.processing_metadata,
        }


class RecognitionService:
    """Main recognition service that orchestrates the pipeline."""

    def __init__(
        self,
        detector: PlateDetector | None = None,
        preprocessor: PreprocessingPipeline | None = None,
        ocr_engine: OCREngine | None = None,
        validator: PlateValidator | None = None,
        config: RecognitionConfig | None = None,
    ):
        self.config = config or RecognitionConfig()
        self.preprocessor = preprocessor or PreprocessingPipeline(
            self.config.preprocessing_config
        )
        self.ocr_engine = ocr_engine or EasyOCREngine(
            languages=self.config.ocr_languages,
            gpu=self.config.ocr_gpu,
            min_confidence=self.config.min_ocr_confidence,
        )
        self.validator = validator or PlateValidator(
            registry=PlateFormatRegistry()
        )

        # Initialize detector (lazy load for YOLO to avoid slow startup)
        self._detector = detector
        self._detector_initialized = detector is not None

    @property
    def detector(self) -> PlateDetector:
        """Lazy load the plate detector."""
        if not self._detector_initialized:
            if self.config.use_plate_detection:
                try:
                    self._detector = YOLOPlateDetector(
                        model_path=self.config.plate_detection_model,
                        confidence_threshold=self.config.detection_confidence,
                    )
                    logger.info("YOLO plate detector initialized")
                except Exception as e:
                    logger.warning(f"Failed to load YOLO detector: {e}, using fallback")
                    self._detector = FallbackDetector()
            else:
                self._detector = FallbackDetector()
            self._detector_initialized = True
        return self._detector

    def process_image(self, image_path: str | Path) -> RecognitionResult:
        """Process an image through the full recognition pipeline.

        Args:
            image_path: Path to the image file

        Returns:
            RecognitionResult with all metadata
        """
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        return self.process_image_array(image)

    def _is_plate_crop(self, image: np.ndarray) -> bool:
        """Detect if the image is already a tightly cropped plate.

        Heuristics: small dimensions with plate-like aspect ratio (wide and short).
        """
        h, w = image.shape[:2]
        if h == 0:
            return False
        aspect_ratio = w / h

        # Plate crops are typically small and have a wide aspect ratio (2:1 to 6:1)
        is_small = w < 800 and h < 300
        is_plate_aspect = 1.5 <= aspect_ratio <= 7.0

        return is_small and is_plate_aspect

    def process_image_array(self, image: np.ndarray) -> RecognitionResult:
        """Process a numpy array image through the recognition pipeline."""
        processing_metadata = {"attempts": 0, "stages_applied": []}

        # Stage 1: Assess image quality
        quality = self.preprocessor.assess_quality(image)
        processing_metadata["quality"] = {
            "blur_score": quality.blur_score,
            "contrast_score": quality.contrast_score,
            "noise_level": quality.noise_level,
            "is_skewed": quality.is_skewed,
        }

        # Stage 2: Detect plate region (skip if image is already a plate crop)
        if self._is_plate_crop(image):
            # Image looks like it's already cropped to the plate — use as-is
            detection_confidence = 0.8
            bounding_box = None
            plate_image = image
            processing_metadata["stages_applied"].append("pre_cropped_plate")
            logger.info("Image detected as pre-cropped plate, skipping detection")
        else:
            detection = self.detector.detect(image)
            if detection:
                detection_confidence = detection.confidence
                bounding_box = detection.bounding_box.to_dict()
                plate_image = self.detector.crop_plate(
                    image, detection, padding=self.config.detection_padding
                )
                processing_metadata["stages_applied"].append("detection")
            else:
                # Use full image as fallback
                detection_confidence = 0.5
                bounding_box = None
                plate_image = image
                processing_metadata["stages_applied"].append("fallback_full_image")

        # Stage 3: Run initial OCR
        ocr_result = self.ocr_engine.extract_text(plate_image)
        processing_metadata["attempts"] += 1

        # Stage 4: Validate and get initial result
        validation = self._validate_ocr_result(ocr_result)

        # Stage 5: Calculate initial confidence
        overall_confidence = self._calculate_confidence(
            detection_confidence, ocr_result.confidence, validation.confidence
        )

        # Stage 6: Retry with preprocessing if confidence is low
        if (
            self.config.enable_enhanced_retry
            and overall_confidence < self.config.needs_review_threshold
            and processing_metadata["attempts"] < self.config.max_processing_attempts
        ):
            enhanced_result = self._retry_with_preprocessing(
                plate_image, detection_confidence, processing_metadata
            )
            if enhanced_result and enhanced_result.confidence_score > overall_confidence:
                return enhanced_result

        # Determine if needs review
        needs_review = self._should_flag_for_review(
            detection_confidence, ocr_result.confidence, validation.confidence
        )

        return RecognitionResult(
            plate_number=validation.text if validation.is_valid or validation.confidence > 0.3 else None,
            confidence_score=overall_confidence,
            detection_confidence=detection_confidence,
            ocr_confidence=ocr_result.confidence,
            bounding_box=bounding_box,
            plate_region=validation.region,
            needs_review=needs_review,
            processing_metadata=processing_metadata,
        )

    def _extract_plate_substrings(self, text: str, confidence: float) -> list[tuple[str, float]]:
        """Extract plate-like substrings from text that may contain extra words.

        On cropped plates, EasyOCR may read extra text like "BRASIL" alongside the
        plate number. This extracts substrings matching known plate patterns.
        """
        cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
        extracted = []

        # Brazilian plate patterns to search for within the text
        patterns = [
            r"[A-Z]{3}\d[A-Z]\d{2}",  # Mercosul: ABC1D23
            r"[A-Z]{3}\d{4}",          # Old format: ABC1234
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, cleaned):
                plate = match.group()
                if not any(e[0] == plate for e in extracted):
                    extracted.append((plate, confidence * 0.95))

        return extracted

    def _validate_ocr_result(self, ocr_result: OCRResult) -> ValidationResult:
        """Validate OCR result using the validator."""
        candidates = self.ocr_engine.get_candidates(
            ocr_result, min_confidence=self.config.min_ocr_confidence
        )

        # Also include the combined text as a candidate, since EasyOCR may
        # split a single plate into multiple text segments (e.g. "ABC" + "1D23").
        # The combined text often forms the full plate number.
        if ocr_result.text and ocr_result.confidence >= self.config.min_ocr_confidence:
            combined = ocr_result.text
            if not any(c[0] == combined for c in candidates):
                candidates.append((combined, ocr_result.confidence))

        # Also try concatenating adjacent OCR segments, since a plate number
        # may be split across 2-3 text detections (e.g. "ABC" + "1D23").
        raw = ocr_result.raw_results
        for i in range(len(raw)):
            for j in range(i + 2, min(i + 4, len(raw) + 1)):
                segment_texts = [r[1] for r in raw[i:j] if r[2] >= self.config.min_ocr_confidence]
                if len(segment_texts) == j - i:
                    concat = "".join(segment_texts)
                    avg_conf = sum(r[2] for r in raw[i:j]) / (j - i)
                    if not any(c[0] == concat for c in candidates):
                        candidates.append((concat, avg_conf))

        # Extract plate patterns from longer text that may include extra words
        # (e.g. "BRASIL ABC1D23" → "ABC1D23")
        for text, conf in list(candidates):
            extracted = self._extract_plate_substrings(text, conf)
            for ext_text, ext_conf in extracted:
                if not any(c[0] == ext_text for c in candidates):
                    candidates.append((ext_text, ext_conf))

        if not candidates:
            return ValidationResult(
                text="",
                original_text="",
                confidence=0.0,
                region=None,
                format_name=None,
                is_valid=False,
            )

        # Validate each candidate and return best
        result = self.validator.validate_batch(
            candidates, region=self.config.default_region
        )

        if result:
            return result

        # If no valid match, return first candidate with low confidence
        return ValidationResult(
            text=candidates[0][0],
            original_text=candidates[0][0],
            confidence=candidates[0][1] * 0.3,
            region=None,
            format_name=None,
            is_valid=False,
        )

    def _retry_with_preprocessing(
        self,
        plate_image: np.ndarray,
        detection_confidence: float,
        metadata: dict,
    ) -> RecognitionResult | None:
        """Retry OCR with various preprocessing configurations."""
        preprocessing_configs = [
            # Config 1: Standard preprocessing
            {"denoise": "normal", "sharpen": True, "clahe_clip": 2.0},
            # Config 2: Heavy denoising
            {"denoise": "heavy", "sharpen": True, "clahe_clip": 3.0},
            # Config 3: Adaptive threshold
            {"threshold": "adaptive", "block_size": 11, "c": 2},
            # Config 4: Morphological operations
            {"morphology": True, "dilate": 1, "erode": 1},
        ]

        best_result = None
        best_confidence = 0.0

        for config in preprocessing_configs:
            if metadata["attempts"] >= self.config.max_processing_attempts:
                break

            try:
                preprocessed = self.preprocessor.process_with_config(plate_image, config)
                ocr_result = self.ocr_engine.extract_text(preprocessed)
                metadata["attempts"] += 1

                validation = self._validate_ocr_result(ocr_result)
                overall = self._calculate_confidence(
                    detection_confidence, ocr_result.confidence, validation.confidence
                )

                if overall > best_confidence:
                    best_confidence = overall
                    best_result = RecognitionResult(
                        plate_number=validation.text if validation.is_valid or validation.confidence > 0.3 else None,
                        confidence_score=overall,
                        detection_confidence=detection_confidence,
                        ocr_confidence=ocr_result.confidence,
                        bounding_box=None,  # Keep original bounding box
                        plate_region=validation.region,
                        needs_review=self._should_flag_for_review(
                            detection_confidence, ocr_result.confidence, validation.confidence
                        ),
                        processing_metadata=metadata.copy(),
                    )

                # Early exit if we get good enough result
                if best_confidence >= self.config.auto_accept_threshold:
                    metadata["stages_applied"].append(f"preprocessing_{config}")
                    break

            except Exception as e:
                logger.warning(f"Preprocessing with config {config} failed: {e}")
                continue

        return best_result

    def _calculate_confidence(
        self,
        detection_conf: float,
        ocr_conf: float,
        validation_conf: float,
    ) -> float:
        """Calculate weighted overall confidence score."""
        # Weights: detection=0.3, ocr=0.4, validation=0.3
        return detection_conf * 0.3 + ocr_conf * 0.4 + validation_conf * 0.3

    def _should_flag_for_review(
        self,
        detection_conf: float,
        ocr_conf: float,
        validation_conf: float,
    ) -> bool:
        """Determine if result needs human review."""
        overall = self._calculate_confidence(detection_conf, ocr_conf, validation_conf)
        return overall < self.config.needs_review_threshold

    # Legacy compatibility methods

    def extract_plate_text(self, image_path: str | Path) -> str | None:
        """Legacy method for backward compatibility.

        Extracts plate text from an image file.
        """
        result = self.process_image(image_path)
        return result.plate_number

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Legacy preprocessing for backward compatibility."""
        return self.preprocessor.get_grayscale_preprocessed(image)


# Singleton instance
_recognition_service: RecognitionService | None = None


def get_recognition_service() -> RecognitionService:
    """Get or create the singleton recognition service."""
    global _recognition_service
    if _recognition_service is None:
        _recognition_service = RecognitionService()
    return _recognition_service
