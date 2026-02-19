"""Image quality assessment for adaptive preprocessing."""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ImageQuality:
    """Results of image quality assessment."""

    blur_score: float  # 0-1, higher is sharper
    contrast_score: float  # 0-1, higher is better contrast
    brightness_score: float  # 0-1, normalized brightness
    noise_level: float  # 0-1, higher means more noise
    is_skewed: bool  # Whether the image appears to be tilted


class ImageQualityAssessor:
    """Assesses image quality to determine preprocessing needs."""

    def __init__(
        self,
        blur_laplacian_threshold: float = 500.0,
        contrast_std_threshold: float = 1000.0,
        noise_threshold: float = 10.0,
        skew_angle_threshold: float = 5.0,
    ):
        self.blur_laplacian_threshold = blur_laplacian_threshold
        self.contrast_std_threshold = contrast_std_threshold
        self.noise_threshold = noise_threshold
        self.skew_angle_threshold = skew_angle_threshold

    def assess(self, image: np.ndarray) -> ImageQuality:
        """Assess image quality metrics."""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        blur_score = self._assess_blur(gray)
        contrast_score = self._assess_contrast(gray)
        brightness_score = self._assess_brightness(gray)
        noise_level = self._estimate_noise(gray)
        is_skewed = self._detect_skew(gray)

        return ImageQuality(
            blur_score=blur_score,
            contrast_score=contrast_score,
            brightness_score=brightness_score,
            noise_level=noise_level,
            is_skewed=is_skewed,
        )

    def _assess_blur(self, gray: np.ndarray) -> float:
        """Assess image sharpness using Laplacian variance.

        Higher values indicate sharper images.
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        # Normalize to 0-1 range
        score = min(variance / self.blur_laplacian_threshold, 1.0)
        return float(score)

    def _assess_contrast(self, gray: np.ndarray) -> float:
        """Assess image contrast using histogram spread."""
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        std = np.std(hist)
        # Normalize to 0-1 range
        score = min(std / self.contrast_std_threshold, 1.0)
        return float(score)

    def _assess_brightness(self, gray: np.ndarray) -> float:
        """Assess average brightness normalized to 0-1."""
        mean_brightness = np.mean(gray) / 255.0
        return float(mean_brightness)

    def _estimate_noise(self, gray: np.ndarray) -> float:
        """Estimate noise level using the median absolute deviation method."""
        # Apply Laplacian to detect high-frequency noise
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        # Use median absolute deviation as noise estimate
        median = np.median(np.abs(laplacian))
        # Normalize to 0-1 range
        noise = min(median / self.noise_threshold, 1.0)
        return float(noise)

    def _detect_skew(self, gray: np.ndarray) -> bool:
        """Detect if the image is significantly skewed."""
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Use Hough Line Transform to detect lines
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=gray.shape[1] // 4,
            maxLineGap=10,
        )

        if lines is None or len(lines) == 0:
            return False

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Avoid division by zero
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Normalize to -45 to 45 range (for near-horizontal lines)
                if abs(angle) < 45:
                    angles.append(angle)

        if not angles:
            return False

        # Get median angle
        median_angle = np.median(angles)
        return abs(median_angle) > self.skew_angle_threshold
