from __future__ import annotations

import math

import cv2
import numpy as np

from .models import Bubble, BubbleScore, ScoringParams
from .preprocess import create_dark_ink_mask, to_gray


def bubble_inner_mask(shape: tuple[int, int], bubble: Bubble, params: ScoringParams) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    axes = (
        max(1, int(round(bubble.rx * params.inner_rx_scale))),
        max(1, int(round(bubble.ry * params.inner_ry_scale))),
    )
    center = (int(round(bubble.cx)), int(round(bubble.cy)))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, thickness=-1)
    return mask


def _component_area_ratio(masked_dark: np.ndarray, mask_area: int, min_pixels: int) -> float:
    if mask_area <= 0:
        return 0.0
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(masked_dark)
    largest = 0
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_pixels:
            largest = max(largest, area)
    return float(largest / mask_area)


def score_bubble(aligned_bgr: np.ndarray, bubble: Bubble, params: ScoringParams) -> BubbleScore:
    gray = to_gray(aligned_bgr)
    darkness = (255.0 - gray.astype(np.float32)) / 255.0
    mask = bubble_inner_mask(gray.shape, bubble, params)
    mask_bool = mask > 0
    mask_area = int(mask_bool.sum())
    if mask_area == 0:
        return BubbleScore(
            option=bubble.option,
            score=0.0,
            ink_ratio=0.0,
            mean_darkness=0.0,
            strong_dark_ratio=0.0,
            component_area_ratio=0.0,
        )

    ink_mask = create_dark_ink_mask(aligned_bgr, dark_pixel_threshold=params.dark_pixel_threshold)
    strong_mask = create_dark_ink_mask(
        aligned_bgr, dark_pixel_threshold=params.strong_dark_threshold
    )
    masked_ink = (ink_mask > 0) & mask_bool
    masked_strong = (strong_mask > 0) & mask_bool
    ink_ratio = float(masked_ink.sum() / mask_area)
    strong_dark_ratio = float(masked_strong.sum() / mask_area)
    mean_darkness = float(darkness[mask_bool].mean())
    component_area_ratio = _component_area_ratio(
        (masked_ink.astype(np.uint8) * 255), mask_area, params.min_component_pixels
    )

    values = {
        "ink_ratio": ink_ratio,
        "mean_darkness": mean_darkness,
        "strong_dark_ratio": strong_dark_ratio,
        "component_area_ratio": component_area_ratio,
    }
    score = 0.0
    for name, weight in params.weights.normalized_items():
        score += weight * values[name]
    score = float(max(0.0, min(1.0, score)))

    return BubbleScore(
        option=bubble.option,
        score=score,
        ink_ratio=ink_ratio,
        mean_darkness=mean_darkness,
        strong_dark_ratio=strong_dark_ratio,
        component_area_ratio=component_area_ratio,
        is_faint=False,
        is_strong=False,
        state="empty",
    )


def score_question_bubbles(
    aligned_bgr: np.ndarray, bubbles: list[Bubble], params: ScoringParams
) -> list[BubbleScore]:
    return [score_bubble(aligned_bgr, bubble, params) for bubble in bubbles]
