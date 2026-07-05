from __future__ import annotations

import cv2
import numpy as np

from .models import AlignedSheet, AlignmentParams, Template
from .preprocess import normalize_image, to_gray


def _order_points(points: np.ndarray) -> np.ndarray:
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(diffs)]
    ordered[3] = points[np.argmax(diffs)]
    return ordered


def _detect_corner_markers_by_contours(
    image: np.ndarray, params: AlignmentParams
) -> tuple[list[tuple[float, float]], dict[str, float]]:
    gray = to_gray(image)
    _, threshold = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
    h, w = gray.shape
    margin_x = int(w * params.marker_search_margin)
    margin_y = int(h * params.marker_search_margin)
    windows = {
        "top_left": (0, 0, margin_x, margin_y),
        "top_right": (w - margin_x, 0, w, margin_y),
        "bottom_right": (w - margin_x, h - margin_y, w, h),
        "bottom_left": (0, h - margin_y, margin_x, h),
    }

    points: list[tuple[float, float]] = []
    diagnostics: dict[str, float] = {}
    for name, (x0, y0, x1, y1) in windows.items():
        crop = threshold[y0:y1, x0:x1]
        contours, _ = cv2.findContours(crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        best: tuple[float, float, float] | None = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 120:
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter <= 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            x, y, width, height = cv2.boundingRect(contour)
            if abs(width - height) > 6:
                continue
            if circularity < 0.78:
                continue
            score = float(area * circularity)
            center = (x0 + x + width / 2.0, y0 + y + height / 2.0)
            if best is None or score > best[0]:
                best = (score, center[0], center[1])
        if best is None:
            return [], diagnostics
        diagnostics[f"{name}_score"] = best[0]
        points.append((best[1], best[2]))
    return points, diagnostics


def _detect_corner_markers_by_hough(
    image: np.ndarray, params: AlignmentParams
) -> tuple[list[tuple[float, float]], dict[str, float]]:
    gray = to_gray(image)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min(image.shape[:2]) * 0.25,
        param1=100,
        param2=18,
        minRadius=params.circle_min_radius,
        maxRadius=params.circle_max_radius,
    )
    diagnostics: dict[str, float] = {}
    if circles is None:
        return [], diagnostics

    candidates = np.round(circles[0, :, :3]).astype(int)
    h, w = gray.shape
    margin_x = int(w * params.marker_search_margin)
    margin_y = int(h * params.marker_search_margin)
    quadrants = {
        "top_left": lambda x, y: x <= margin_x and y <= margin_y,
        "top_right": lambda x, y: x >= w - margin_x and y <= margin_y,
        "bottom_right": lambda x, y: x >= w - margin_x and y >= h - margin_y,
        "bottom_left": lambda x, y: x <= margin_x and y >= h - margin_y,
    }

    selected: list[tuple[float, float]] = []
    darkness_scores: list[float] = []
    for name, predicate in quadrants.items():
        matches = []
        for x, y, radius in candidates:
            if predicate(x, y):
                y0 = max(0, y - radius)
                y1 = min(h, y + radius)
                x0 = max(0, x - radius)
                x1 = min(w, x + radius)
                patch = gray[y0:y1, x0:x1]
                darkness = float(1.0 - patch.mean() / 255.0) if patch.size else 0.0
                corner_distance = float(
                    np.hypot(x if "left" in name else w - x, y if "top" in name else h - y)
                )
                matches.append((darkness - 0.002 * corner_distance, darkness, x, y))
        if not matches:
            return [], diagnostics
        matches.sort(reverse=True)
        _, darkness, x, y = matches[0]
        selected.append((float(x), float(y)))
        darkness_scores.append(darkness)
        diagnostics[f"{name}_darkness"] = darkness

    diagnostics["marker_darkness_mean"] = float(np.mean(darkness_scores))
    return selected, diagnostics


def detect_corner_markers(
    image: np.ndarray, params: AlignmentParams
) -> tuple[list[tuple[float, float]], dict[str, float]]:
    contour_points, contour_diagnostics = _detect_corner_markers_by_contours(image, params)
    if len(contour_points) == 4:
        contour_diagnostics["method"] = "corner_contours"
        return contour_points, contour_diagnostics

    hough_points, hough_diagnostics = _detect_corner_markers_by_hough(image, params)
    hough_diagnostics["method"] = "marker_hough"
    return hough_points, hough_diagnostics


def align_sheet(image: np.ndarray, template: Template, params: AlignmentParams) -> AlignedSheet:
    normalized = normalize_image(image)
    width = params.output_width or template.reference_size.width
    height = params.output_height or template.reference_size.height
    diagnostics: dict[str, float | int | str] = {}

    if not template.alignment.reference_points:
        resized = cv2.resize(normalized, (width, height), interpolation=cv2.INTER_LINEAR)
        return AlignedSheet(
            image=resized,
            homography=None,
            status="low_confidence",
            confidence=0.35,
            method="resize_fallback",
            diagnostics={"reason": "missing_reference_points"},
        )

    src_points, marker_diagnostics = detect_corner_markers(normalized, params)
    diagnostics.update(marker_diagnostics)
    if len(src_points) != 4:
        resized = cv2.resize(normalized, (width, height), interpolation=cv2.INTER_LINEAR)
        return AlignedSheet(
            image=resized,
            homography=None,
            status="failed",
            confidence=0.0,
            method="marker_hough",
            diagnostics={"reason": "markers_not_found", **diagnostics},
        )

    src = _order_points(np.array(src_points, dtype=np.float32))
    dst = _order_points(
        np.array([(point.x, point.y) for point in template.alignment.reference_points], dtype=np.float32)
    )
    homography = cv2.getPerspectiveTransform(src, dst)
    aligned = cv2.warpPerspective(normalized, homography, (width, height))
    if diagnostics.get("method") == "corner_contours":
        scores = [float(value) for key, value in diagnostics.items() if key.endswith("_score")]
        confidence = float(min(1.0, max(0.0, np.mean(scores) / 780.0))) if scores else 0.85
    else:
        confidence = float(min(1.0, max(0.0, diagnostics.get("marker_darkness_mean", 0.0) + 0.45)))
    status = "ok" if confidence >= params.min_confidence else "low_confidence"
    diagnostics["source_points_found"] = len(src_points)

    return AlignedSheet(
        image=aligned,
        homography=homography,
        status=status,
        confidence=confidence,
        method=str(diagnostics.get("method", "marker_hough")),
        diagnostics=diagnostics,
    )
