"""YOLOv8-based plate detector."""

import logging
from pathlib import Path

import numpy as np

from app.services.detection.detector import (
    BoundingBox,
    DetectionResult,
    PlateDetector,
)

logger = logging.getLogger(__name__)


class YOLOPlateDetector(PlateDetector):
    """License plate detector using YOLOv8.

    Uses ultralytics YOLO for object detection. Can work with:
    - Pre-trained YOLO models (yolov8n.pt, yolov8s.pt, etc.)
    - Custom-trained license plate detection models
    """

    def __init__(
        self,
        model_path: str | Path = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str | None = None,
    ):
        """Initialize the YOLO plate detector.

        Args:
            model_path: Path to YOLO model weights or model name
            confidence_threshold: Minimum confidence for detections
            device: Device to run inference on ('cpu', 'cuda', etc.)
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        self._model = None

        # Class names that indicate license plates
        # These are checked against the model's class names
        self.plate_class_names = {
            "license_plate",
            "license plate",
            "plate",
            "number_plate",
            "number plate",
            "car_plate",
            "vehicle_plate",
        }

    @property
    def model(self):
        """Lazy load the YOLO model."""
        if self._model is None:
            try:
                from ultralytics import YOLO

                logger.info(f"Loading YOLO model from {self.model_path}")
                self._model = YOLO(str(self.model_path))
                if self.device:
                    self._model.to(self.device)
                logger.info("YOLO model loaded successfully")
            except ImportError:
                logger.warning(
                    "ultralytics not installed. Install with: pip install ultralytics"
                )
                raise
        return self._model

    def detect(self, image: np.ndarray) -> DetectionResult | None:
        """Detect the most confident license plate in the image."""
        detections = self.detect_all(image)
        if not detections:
            return None
        # Return highest confidence detection
        return max(detections, key=lambda d: d.confidence)

    def detect_all(self, image: np.ndarray) -> list[DetectionResult]:
        """Detect all license plates in the image."""
        try:
            results = self.model.predict(
                source=image,
                conf=self.confidence_threshold,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"YOLO prediction failed: {e}")
            return []

        if not results or len(results) == 0:
            return []

        detections = []
        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            return []

        boxes = result.boxes

        for i in range(len(boxes)):
            # Get bounding box coordinates
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())

            # Get class name
            class_name = result.names.get(cls_id, "unknown")

            # Check if this is a plate detection
            # For general object detection models, we might detect vehicles
            # For license plate specific models, we detect plates directly
            is_plate = self._is_plate_class(class_name)
            is_vehicle = class_name.lower() in {"car", "truck", "bus", "vehicle"}

            if is_plate or is_vehicle:
                bbox = BoundingBox.from_xyxy(
                    int(xyxy[0]),
                    int(xyxy[1]),
                    int(xyxy[2]),
                    int(xyxy[3]),
                )

                detections.append(
                    DetectionResult(
                        bounding_box=bbox,
                        confidence=conf,
                        class_name=class_name,
                    )
                )

        # Sort by confidence (highest first)
        detections.sort(key=lambda d: d.confidence, reverse=True)

        return detections

    def _is_plate_class(self, class_name: str) -> bool:
        """Check if the class name indicates a license plate."""
        name_lower = class_name.lower().replace("-", "_").replace(" ", "_")
        return name_lower in self.plate_class_names or "plate" in name_lower


class FallbackDetector(PlateDetector):
    """Fallback detector that returns the full image as the detected region.

    Used when no proper plate detector is available.
    """

    def __init__(self, padding_ratio: float = 0.1):
        """Initialize fallback detector.

        Args:
            padding_ratio: Ratio of padding to remove from edges (0-0.5)
        """
        self.padding_ratio = min(0.5, max(0, padding_ratio))

    def detect(self, image: np.ndarray) -> DetectionResult | None:
        """Return the center region of the image."""
        h, w = image.shape[:2]

        # Apply padding to focus on center
        pad_x = int(w * self.padding_ratio)
        pad_y = int(h * self.padding_ratio)

        return DetectionResult(
            bounding_box=BoundingBox(
                x=pad_x,
                y=pad_y,
                width=w - 2 * pad_x,
                height=h - 2 * pad_y,
            ),
            confidence=0.5,  # Low confidence since this is a fallback
            class_name="fallback_region",
        )

    def detect_all(self, image: np.ndarray) -> list[DetectionResult]:
        """Return single detection covering center of image."""
        result = self.detect(image)
        return [result] if result else []
