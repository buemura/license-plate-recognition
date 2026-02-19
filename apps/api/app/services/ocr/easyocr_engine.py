"""EasyOCR-based OCR engine."""

import logging

import numpy as np

from app.services.ocr.engine import CharacterResult, OCREngine, OCRResult

logger = logging.getLogger(__name__)


class EasyOCREngine(OCREngine):
    """OCR engine using EasyOCR."""

    def __init__(
        self,
        languages: list[str] | None = None,
        gpu: bool = False,
        min_confidence: float = 0.3,
    ):
        """Initialize EasyOCR engine.

        Args:
            languages: List of language codes (default: ['en'])
            gpu: Whether to use GPU acceleration
            min_confidence: Minimum confidence threshold for results
        """
        self.languages = languages or ["en"]
        self.gpu = gpu
        self.min_confidence = min_confidence
        self._reader = None

    @property
    def reader(self):
        """Lazy load the EasyOCR reader."""
        if self._reader is None:
            import easyocr

            logger.info(f"Initializing EasyOCR with languages: {self.languages}")
            self._reader = easyocr.Reader(self.languages, gpu=self.gpu)
            logger.info("EasyOCR initialized successfully")
        return self._reader

    def extract_text(self, image: np.ndarray) -> OCRResult:
        """Extract text from an image using EasyOCR."""
        try:
            results = self.reader.readtext(image, detail=1, paragraph=False)
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                characters=[],
                bounding_boxes=[],
                raw_results=[],
            )

        if not results:
            return OCRResult(
                text="",
                confidence=0.0,
                characters=[],
                bounding_boxes=[],
                raw_results=[],
            )

        # Process results
        all_text = []
        all_chars = []
        all_boxes = []
        total_confidence = 0.0
        valid_count = 0
        current_position = 0

        for bbox, text, conf in results:
            if conf < self.min_confidence:
                continue

            all_text.append(text)
            all_boxes.append(self._bbox_to_dict(bbox))
            total_confidence += conf
            valid_count += 1

            # Create character results (estimate per-character confidence)
            for i, char in enumerate(text):
                all_chars.append(
                    CharacterResult(
                        char=char,
                        confidence=conf,  # Use word confidence for each char
                        position=current_position + i,
                    )
                )

            current_position += len(text)

        combined_text = "".join(all_text)
        avg_confidence = total_confidence / valid_count if valid_count > 0 else 0.0

        return OCRResult(
            text=combined_text,
            confidence=avg_confidence,
            characters=all_chars,
            bounding_boxes=all_boxes,
            raw_results=results,
        )

    def _bbox_to_dict(self, bbox: list) -> dict:
        """Convert EasyOCR bounding box to dictionary.

        EasyOCR returns bounding boxes as [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
        """
        if not bbox or len(bbox) < 4:
            return {}

        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]

        return {
            "x": int(min(x_coords)),
            "y": int(min(y_coords)),
            "width": int(max(x_coords) - min(x_coords)),
            "height": int(max(y_coords) - min(y_coords)),
        }
