"""Abstract plate detector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class BoundingBox:
    """Bounding box coordinates for detected plate."""

    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_xyxy(cls, x1: int, y1: int, x2: int, y2: int) -> "BoundingBox":
        """Create from corner coordinates (x1, y1, x2, y2)."""
        return cls(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
        )

    def to_xyxy(self) -> tuple[int, int, int, int]:
        """Convert to corner coordinates (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def add_padding(self, padding: int, image_shape: tuple[int, int]) -> "BoundingBox":
        """Add padding to bounding box, clamped to image dimensions."""
        h, w = image_shape[:2]
        return BoundingBox(
            x=max(0, self.x - padding),
            y=max(0, self.y - padding),
            width=min(w - max(0, self.x - padding), self.width + 2 * padding),
            height=min(h - max(0, self.y - padding), self.height + 2 * padding),
        )


@dataclass
class DetectionResult:
    """Result of plate detection."""

    bounding_box: BoundingBox
    confidence: float
    class_name: str = "license_plate"


class PlateDetector(ABC):
    """Abstract base class for plate detectors."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> DetectionResult | None:
        """Detect license plate in image.

        Args:
            image: Input image as numpy array (BGR format)

        Returns:
            DetectionResult if plate found, None otherwise
        """
        pass

    @abstractmethod
    def detect_all(self, image: np.ndarray) -> list[DetectionResult]:
        """Detect all license plates in image.

        Args:
            image: Input image as numpy array (BGR format)

        Returns:
            List of DetectionResult for all detected plates
        """
        pass

    def crop_plate(
        self,
        image: np.ndarray,
        detection: DetectionResult,
        padding: int = 10,
    ) -> np.ndarray:
        """Crop the plate region from the image.

        Args:
            image: Input image
            detection: Detection result with bounding box
            padding: Extra padding around the plate
        """
        bbox = detection.bounding_box.add_padding(padding, image.shape)
        x1, y1, x2, y2 = bbox.to_xyxy()
        return image[y1:y2, x1:x2].copy()
