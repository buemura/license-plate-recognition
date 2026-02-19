"""Preprocessing pipeline orchestrator."""

from dataclasses import dataclass

import cv2
import numpy as np

from app.services.preprocessing.deblur import DeblurProcessor
from app.services.preprocessing.enhance import ContrastEnhancer
from app.services.preprocessing.perspective import PerspectiveCorrector
from app.services.preprocessing.quality import ImageQuality, ImageQualityAssessor


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing pipeline."""

    # Quality thresholds for triggering preprocessing
    blur_threshold: float = 0.3
    contrast_threshold: float = 0.4
    noise_threshold: float = 0.3
    brightness_low: float = 0.2
    brightness_high: float = 0.8

    # Output normalization
    target_width: int = 300
    target_height: int = 100

    # Enable/disable stages
    enable_deblur: bool = True
    enable_enhance: bool = True
    enable_perspective: bool = True
    enable_normalize: bool = True


class PreprocessingPipeline:
    """Orchestrates image preprocessing stages."""

    def __init__(self, config: PreprocessingConfig | None = None):
        self.config = config or PreprocessingConfig()
        self.quality_assessor = ImageQualityAssessor()
        self.deblur = DeblurProcessor()
        self.enhance = ContrastEnhancer()
        self.perspective = PerspectiveCorrector()

    def assess_quality(self, image: np.ndarray) -> ImageQuality:
        """Assess image quality to determine preprocessing needs."""
        return self.quality_assessor.assess(image)

    def process(
        self,
        image: np.ndarray,
        quality: ImageQuality | None = None,
        force_all: bool = False,
    ) -> np.ndarray:
        """Apply appropriate preprocessing based on quality assessment.

        Args:
            image: Input image
            quality: Pre-computed quality assessment (will compute if None)
            force_all: If True, apply all preprocessing stages regardless of quality
        """
        if quality is None:
            quality = self.assess_quality(image)

        result = image.copy()

        # Stage 1: Perspective correction (if skewed)
        if self.config.enable_perspective and (force_all or quality.is_skewed):
            result = self.perspective.correct(result)

        # Stage 2: Deblurring (if blur detected)
        if self.config.enable_deblur:
            if force_all or quality.blur_score < self.config.blur_threshold:
                result = self.deblur.sharpen(result)

        # Stage 3: Contrast and brightness enhancement
        if self.config.enable_enhance:
            if force_all or self._needs_enhancement(quality):
                result = self.enhance.enhance_adaptive(result, quality)

        # Stage 4: Normalize to standard size
        if self.config.enable_normalize:
            result = self._normalize_size(result)

        return result

    def process_with_config(
        self, image: np.ndarray, config_overrides: dict
    ) -> np.ndarray:
        """Process with specific configuration overrides.

        Useful for retry attempts with different parameters.
        """
        result = image.copy()

        # Apply denoising
        denoise_strength = config_overrides.get("denoise")
        if denoise_strength:
            result = self.enhance.denoise(result, strength=denoise_strength)

        # Apply sharpening
        if config_overrides.get("sharpen"):
            result = self.deblur.sharpen(result)

        # Apply CLAHE with custom clip limit
        clahe_clip = config_overrides.get("clahe_clip")
        if clahe_clip:
            result = self.enhance.apply_clahe(result, clip_limit=clahe_clip)

        # Apply adaptive thresholding
        if config_overrides.get("threshold") == "adaptive":
            gray = (
                cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                if len(result.shape) == 3
                else result
            )
            block_size = config_overrides.get("block_size", 11)
            c = config_overrides.get("c", 2)
            result = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
            )

        # Apply morphological operations
        if config_overrides.get("morphology"):
            gray = (
                cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                if len(result.shape) == 3
                else result
            )
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilate_iter = config_overrides.get("dilate", 1)
            erode_iter = config_overrides.get("erode", 1)
            result = cv2.dilate(gray, kernel, iterations=dilate_iter)
            result = cv2.erode(result, kernel, iterations=erode_iter)

        return result

    def _needs_enhancement(self, quality: ImageQuality) -> bool:
        """Check if image needs contrast/brightness enhancement."""
        return (
            quality.contrast_score < self.config.contrast_threshold
            or quality.noise_level > self.config.noise_threshold
            or quality.brightness_score < self.config.brightness_low
            or quality.brightness_score > self.config.brightness_high
        )

    def _normalize_size(self, image: np.ndarray) -> np.ndarray:
        """Resize image to standard dimensions."""
        h, w = image.shape[:2]

        # Calculate aspect ratio
        aspect = w / h
        target_aspect = self.config.target_width / self.config.target_height

        if aspect > target_aspect:
            # Image is wider - scale by width
            new_width = self.config.target_width
            new_height = int(new_width / aspect)
        else:
            # Image is taller - scale by height
            new_height = self.config.target_height
            new_width = int(new_height * aspect)

        # Resize
        resized = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
        )

        return resized

    def get_grayscale_preprocessed(self, image: np.ndarray) -> np.ndarray:
        """Apply legacy preprocessing for backward compatibility.

        This matches the original preprocessing from RecognitionService.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Apply bilateral filter
        denoised = cv2.bilateralFilter(enhanced, 11, 17, 17)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        return thresh
