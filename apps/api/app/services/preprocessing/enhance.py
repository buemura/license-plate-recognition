"""Contrast and brightness enhancement processors."""

import cv2
import numpy as np

from app.services.preprocessing.quality import ImageQuality


class ContrastEnhancer:
    """Handles contrast and brightness enhancement."""

    def __init__(
        self,
        clahe_clip_limit: float = 2.0,
        clahe_tile_grid_size: tuple[int, int] = (8, 8),
        bilateral_d: int = 11,
        bilateral_sigma_color: float = 17,
        bilateral_sigma_space: float = 17,
    ):
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid_size = clahe_tile_grid_size
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space

    def apply_clahe(
        self,
        image: np.ndarray,
        clip_limit: float | None = None,
        tile_grid_size: tuple[int, int] | None = None,
    ) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Args:
            image: Input image (can be color or grayscale)
            clip_limit: Override default clip limit
            tile_grid_size: Override default tile grid size
        """
        clip = clip_limit or self.clahe_clip_limit
        tile = tile_grid_size or self.clahe_tile_grid_size

        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=tile)

        if len(image.shape) == 3:
            # For color images, convert to LAB and apply CLAHE to L channel
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            l_enhanced = clahe.apply(l_channel)
            lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
            return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        else:
            return clahe.apply(image)

    def denoise(self, image: np.ndarray, strength: str = "normal") -> np.ndarray:
        """Apply bilateral filtering for noise reduction while preserving edges.

        Args:
            image: Input image
            strength: 'light', 'normal', or 'heavy'
        """
        strength_params = {
            "light": (9, 12, 12),
            "normal": (self.bilateral_d, self.bilateral_sigma_color, self.bilateral_sigma_space),
            "heavy": (15, 25, 25),
        }

        d, sigma_color, sigma_space = strength_params.get(
            strength,
            (self.bilateral_d, self.bilateral_sigma_color, self.bilateral_sigma_space),
        )

        return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

    def denoise_nlm(self, image: np.ndarray, h: float = 10) -> np.ndarray:
        """Apply Non-local Means denoising (slower but more effective)."""
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, h, 7, 21)

    def adjust_brightness(
        self, image: np.ndarray, target_brightness: float = 0.5
    ) -> np.ndarray:
        """Adjust image brightness to target level.

        Args:
            image: Input image
            target_brightness: Target brightness (0-1)
        """
        # Calculate current brightness
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        current_brightness = np.mean(gray) / 255.0

        # Calculate adjustment factor
        if current_brightness == 0:
            return image

        factor = target_brightness / current_brightness
        factor = np.clip(factor, 0.5, 2.0)  # Limit adjustment range

        # Apply adjustment
        adjusted = cv2.convertScaleAbs(image, alpha=factor, beta=0)
        return adjusted

    def enhance_adaptive(self, image: np.ndarray, quality: ImageQuality) -> np.ndarray:
        """Apply adaptive enhancement based on image quality assessment.

        Args:
            image: Input image
            quality: ImageQuality assessment results
        """
        result = image.copy()

        # Adjust CLAHE clip limit based on contrast score
        if quality.contrast_score < 0.3:
            clip_limit = 4.0  # Aggressive for low contrast
        elif quality.contrast_score < 0.6:
            clip_limit = 2.5  # Moderate
        else:
            clip_limit = 1.5  # Light for good contrast

        # Apply CLAHE
        result = self.apply_clahe(result, clip_limit=clip_limit)

        # Apply denoising if needed
        if quality.noise_level > 0.3:
            denoise_strength = "heavy" if quality.noise_level > 0.6 else "normal"
            result = self.denoise(result, strength=denoise_strength)

        # Adjust brightness if needed
        if quality.brightness_score < 0.3 or quality.brightness_score > 0.7:
            result = self.adjust_brightness(result, target_brightness=0.5)

        return result
