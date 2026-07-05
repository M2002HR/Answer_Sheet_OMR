from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .exceptions import ImageLoadError


def load_image(path: str | Path) -> np.ndarray:
    image_path = str(path)
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(f"Could not read image: {image_path}")
    return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()


def to_gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def remove_shadows_or_normalize_illumination(image: np.ndarray) -> np.ndarray:
    gray = to_gray(image)
    dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
    background = cv2.medianBlur(dilated, 21)
    diff = 255 - cv2.absdiff(gray, background)
    normalized = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)


def create_dark_ink_mask(
    image: np.ndarray,
    dark_pixel_threshold: int = 120,
    strong_color_saturation: int = 60,
) -> np.ndarray:
    gray = to_gray(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    value_mask = gray <= dark_pixel_threshold
    low_value_mask = hsv[:, :, 2] <= dark_pixel_threshold
    cyan_like = (
        (hsv[:, :, 0] >= 75)
        & (hsv[:, :, 0] <= 115)
        & (hsv[:, :, 1] >= strong_color_saturation)
        & (hsv[:, :, 2] >= 90)
    )
    mask = (value_mask | low_value_mask) & ~cyan_like
    return (mask.astype(np.uint8) * 255)
