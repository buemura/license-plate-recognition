"""Abstract OCR engine interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class CharacterResult:
    """Result for a single character from OCR."""

    char: str
    confidence: float
    position: int  # Position in the combined text


@dataclass
class OCRResult:
    """Result from OCR extraction."""

    text: str  # Combined text from all detections
    confidence: float  # Average confidence
    characters: list[CharacterResult] = field(default_factory=list)
    bounding_boxes: list[dict] = field(default_factory=list)
    raw_results: list[tuple] = field(default_factory=list)  # Original OCR output


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """Extract text from an image.

        Args:
            image: Input image as numpy array

        Returns:
            OCRResult with extracted text and metadata
        """
        pass

    def get_low_confidence_positions(
        self, result: OCRResult, threshold: float = 0.5
    ) -> list[int]:
        """Get positions of characters with low confidence.

        Args:
            result: OCR result to analyze
            threshold: Confidence threshold

        Returns:
            List of positions with confidence below threshold
        """
        return [c.position for c in result.characters if c.confidence < threshold]

    def get_candidates(
        self, result: OCRResult, min_confidence: float = 0.3
    ) -> list[tuple[str, float]]:
        """Get text candidates from OCR result.

        Args:
            result: OCR result
            min_confidence: Minimum confidence to include

        Returns:
            List of (text, confidence) tuples sorted by confidence desc
        """
        candidates = []
        for bbox, text, conf in result.raw_results:
            if conf >= min_confidence:
                candidates.append((text, conf))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
