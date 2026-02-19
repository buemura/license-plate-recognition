"""Perspective correction for tilted license plates."""

import cv2
import numpy as np


class PerspectiveCorrector:
    """Handles perspective correction for tilted or skewed plates."""

    def __init__(
        self,
        min_contour_area_ratio: float = 0.1,
        max_skew_angle: float = 45.0,
    ):
        self.min_contour_area_ratio = min_contour_area_ratio
        self.max_skew_angle = max_skew_angle

    def correct(self, image: np.ndarray) -> np.ndarray:
        """Attempt to correct perspective distortion.

        Uses contour detection to find the plate region and
        applies perspective transform to straighten it.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Find plate contour
        plate_contour = self._find_plate_contour(gray)

        if plate_contour is None:
            # Try deskewing using Hough lines instead
            return self._deskew_hough(image)

        # Get perspective transform
        warped = self._apply_perspective_transform(image, plate_contour)

        return warped if warped is not None else image

    def _find_plate_contour(self, gray: np.ndarray) -> np.ndarray | None:
        """Find the largest rectangular contour that could be a plate."""
        # Apply edge detection
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # Filter and sort by area
        image_area = gray.shape[0] * gray.shape[1]
        min_area = image_area * self.min_contour_area_ratio

        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Approximate to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Look for quadrilaterals
                if len(approx) == 4:
                    valid_contours.append((area, approx))

        if not valid_contours:
            return None

        # Return largest valid contour
        valid_contours.sort(key=lambda x: x[0], reverse=True)
        return valid_contours[0][1]

    def _apply_perspective_transform(
        self, image: np.ndarray, contour: np.ndarray
    ) -> np.ndarray | None:
        """Apply perspective transform to straighten the plate."""
        # Order points: top-left, top-right, bottom-right, bottom-left
        points = contour.reshape(4, 2).astype(np.float32)
        ordered = self._order_points(points)

        if ordered is None:
            return None

        # Calculate dimensions of the output rectangle
        width_top = np.linalg.norm(ordered[1] - ordered[0])
        width_bottom = np.linalg.norm(ordered[2] - ordered[3])
        width = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(ordered[3] - ordered[0])
        height_right = np.linalg.norm(ordered[2] - ordered[1])
        height = int(max(height_left, height_right))

        if width < 10 or height < 10:
            return None

        # Define destination points
        dst = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1],
            ],
            dtype=np.float32,
        )

        # Get perspective transform matrix
        matrix = cv2.getPerspectiveTransform(ordered, dst)

        # Apply transform
        warped = cv2.warpPerspective(image, matrix, (width, height))

        return warped

    def _order_points(self, points: np.ndarray) -> np.ndarray | None:
        """Order points as: top-left, top-right, bottom-right, bottom-left."""
        if len(points) != 4:
            return None

        # Sort by y-coordinate
        sorted_by_y = points[np.argsort(points[:, 1])]

        # Top two points
        top = sorted_by_y[:2]
        # Sort by x-coordinate
        top = top[np.argsort(top[:, 0])]

        # Bottom two points
        bottom = sorted_by_y[2:]
        # Sort by x-coordinate
        bottom = bottom[np.argsort(bottom[:, 0])]

        return np.array([top[0], top[1], bottom[1], bottom[0]], dtype=np.float32)

    def _deskew_hough(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using Hough line detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=gray.shape[1] // 4,
            maxLineGap=10,
        )

        if lines is None or len(lines) == 0:
            return image

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Only consider near-horizontal lines
                if abs(angle) < self.max_skew_angle:
                    angles.append(angle)

        if not angles:
            return image

        # Get median angle for rotation
        median_angle = np.median(angles)

        if abs(median_angle) < 0.5:
            return image

        # Rotate image
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)

        # Calculate new bounding box size
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Adjust rotation matrix
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]

        rotated = cv2.warpAffine(
            image, rotation_matrix, (new_w, new_h), borderValue=(255, 255, 255)
        )

        return rotated
