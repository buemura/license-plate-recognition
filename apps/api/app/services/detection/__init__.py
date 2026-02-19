from app.services.detection.detector import (
    BoundingBox,
    DetectionResult,
    PlateDetector,
)
from app.services.detection.yolo_detector import YOLOPlateDetector

__all__ = [
    "BoundingBox",
    "DetectionResult",
    "PlateDetector",
    "YOLOPlateDetector",
]
