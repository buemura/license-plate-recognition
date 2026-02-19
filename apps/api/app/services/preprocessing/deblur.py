"""Image deblurring and sharpening processors."""

import cv2
import numpy as np


class DeblurProcessor:
    """Handles deblurring and sharpening of images."""

    def __init__(
        self,
        unsharp_sigma: float = 3.0,
        unsharp_strength: float = 1.5,
        wiener_kernel_size: int = 15,
        wiener_noise_var: float = 0.01,
    ):
        self.unsharp_sigma = unsharp_sigma
        self.unsharp_strength = unsharp_strength
        self.wiener_kernel_size = wiener_kernel_size
        self.wiener_noise_var = wiener_noise_var

    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Apply unsharp masking for general sharpening.

        Good for mild blur and improving edge definition.
        """
        # Create Gaussian blurred version
        gaussian = cv2.GaussianBlur(image, (0, 0), self.unsharp_sigma)

        # Unsharp mask: original + strength * (original - blurred)
        sharpened = cv2.addWeighted(
            image,
            self.unsharp_strength,
            gaussian,
            -(self.unsharp_strength - 1),
            0,
        )

        return sharpened

    def deblur_motion(self, image: np.ndarray, angle: float = 0) -> np.ndarray:
        """Apply Wiener deconvolution for motion blur.

        Args:
            image: Input image
            angle: Estimated motion blur angle in degrees (0 = horizontal)
        """
        # Convert to grayscale if color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Create motion blur kernel estimate
        kernel = self._create_motion_kernel(self.wiener_kernel_size, angle)

        # Pad kernel to image size
        kernel_padded = np.zeros_like(gray, dtype=np.float64)
        kh, kw = kernel.shape
        kernel_padded[:kh, :kw] = kernel

        # Apply Wiener deconvolution in frequency domain
        gray_float = gray.astype(np.float64)
        f_image = np.fft.fft2(gray_float)
        f_kernel = np.fft.fft2(kernel_padded)

        # Wiener filter: H* / (|H|^2 + noise_var)
        wiener = np.conj(f_kernel) / (np.abs(f_kernel) ** 2 + self.wiener_noise_var)
        f_result = f_image * wiener

        # Convert back to spatial domain
        result = np.fft.ifft2(f_result)
        result = np.abs(result)

        # Normalize to uint8
        result = np.clip(result, 0, 255).astype(np.uint8)

        return result

    def _create_motion_kernel(self, size: int, angle: float) -> np.ndarray:
        """Create a motion blur kernel at the specified angle."""
        kernel = np.zeros((size, size), dtype=np.float64)
        center = size // 2

        # Create horizontal line
        kernel[center, :] = 1.0

        # Rotate if needed
        if angle != 0:
            rotation_matrix = cv2.getRotationMatrix2D(
                (center, center), angle, 1.0
            )
            kernel = cv2.warpAffine(
                kernel, rotation_matrix, (size, size), flags=cv2.INTER_LINEAR
            )

        # Normalize
        kernel = kernel / kernel.sum()

        return kernel

    def process(self, image: np.ndarray, use_wiener: bool = False) -> np.ndarray:
        """Apply appropriate deblurring based on settings.

        Args:
            image: Input image
            use_wiener: If True, use Wiener deconvolution (slower, for motion blur)
                       If False, use unsharp masking (faster, for general blur)
        """
        if use_wiener:
            return self.deblur_motion(image)
        else:
            return self.sharpen(image)
