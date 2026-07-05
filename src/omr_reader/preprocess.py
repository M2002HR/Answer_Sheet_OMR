from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import cv2
import numpy as np

from .exceptions import ImageLoadError
from .models import PreprocessParams


def _render_pdf_first_page(path: str | Path, pdf_dpi: int) -> np.ndarray:
    pdf_path = Path(path)
    with tempfile.TemporaryDirectory(prefix="omr_pdf_") as tmp_dir:
        output_prefix = Path(tmp_dir) / "page"
        command = [
            "pdftoppm",
            "-f",
            "1",
            "-singlefile",
            "-r",
            str(pdf_dpi),
            "-png",
            str(pdf_path),
            str(output_prefix),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except FileNotFoundError as exc:
            raise ImageLoadError(
                "Could not rasterize PDF because `pdftoppm` is not installed"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
            raise ImageLoadError(f"Could not rasterize PDF {pdf_path}: {stderr}") from exc

        rendered_path = output_prefix.with_suffix(".png")
        image = cv2.imread(str(rendered_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ImageLoadError(f"Could not read rasterized PDF page: {rendered_path}")
        return image


def load_image(path: str | Path, pdf_dpi: int = 200) -> np.ndarray:
    image_path = Path(path)
    if image_path.suffix.lower() == ".pdf":
        return _render_pdf_first_page(image_path, pdf_dpi=pdf_dpi)

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(f"Could not read image: {image_path}")
    return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()


def to_gray(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def enhance_contrast(image: np.ndarray, params: PreprocessParams) -> np.ndarray:
    gray = to_gray(image)
    if params.normalize_illumination:
        dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
        background = cv2.medianBlur(dilated, 21)
        gray = 255 - cv2.absdiff(gray, background)
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    if params.apply_clahe:
        clahe = cv2.createCLAHE(
            clipLimit=params.clahe_clip_limit,
            tileGridSize=(params.clahe_tile_grid_size, params.clahe_tile_grid_size),
        )
        gray = clahe.apply(gray)

    if params.sharpen_amount > 0:
        blurred = cv2.GaussianBlur(gray, (0, 0), 2.0)
        gray = cv2.addWeighted(gray, 1.0 + params.sharpen_amount, blurred, -params.sharpen_amount, 0)

    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def remove_shadows_or_normalize_illumination(
    image: np.ndarray, params: PreprocessParams | None = None
) -> np.ndarray:
    active_params = params or PreprocessParams()
    return enhance_contrast(image, active_params)


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
