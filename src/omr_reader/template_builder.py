from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .alignment import detect_corner_markers
from .exceptions import TemplateValidationError
from .models import AlignmentParams, Bubble, ReferencePoint, ReferenceSize, Template, TemplateAlignment
from .preprocess import load_image


def _cluster_sorted(values: list[float], tolerance: float) -> list[list[float]]:
    clusters: list[list[float]] = []
    for value in sorted(values):
        if not clusters or abs(value - np.mean(clusters[-1])) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return clusters


def detect_cyan_bubble_boxes(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (95, 20, 150), (105, 255, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    raw_boxes: list[tuple[int, int, int, int, float]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if 12 <= w <= 22 and 6 <= h <= 12 and 20 <= area <= 120:
            raw_boxes.append((x, y, w, h, area))

    raw_boxes.sort(key=lambda item: (item[1], item[0], -item[4]))
    deduped: list[tuple[int, int, int, int]] = []
    for x, y, w, h, _ in raw_boxes:
        cx = x + w / 2.0
        cy = y + h / 2.0
        if any(
            abs(cx - (dx + dw / 2.0)) < 2.0 and abs(cy - (dy + dh / 2.0)) < 2.0
            for dx, dy, dw, dh in deduped
        ):
            continue
        deduped.append((x, y, w, h))
    return deduped


def detect_dark_bubble_boxes(
    image: np.ndarray, answer_area: tuple[int, int, int, int] | None = None
) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 180)
    closed = cv2.morphologyEx(
        edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    )
    contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    x_min = y_min = 0
    x_max = image.shape[1]
    y_max = image.shape[0]
    if answer_area is not None:
        area_x, area_y, area_w, area_h = answer_area
        x_min = area_x
        y_min = area_y
        x_max = area_x + area_w
        y_max = area_y + area_h

    raw_boxes: list[tuple[int, int, int, int, float]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            continue
        area = cv2.contourArea(contour)
        aspect_ratio = w / max(h, 1)
        if 14 <= w <= 35 and 6 <= h <= 18 and 1.2 <= aspect_ratio <= 4.5 and 20 <= area <= 280:
            raw_boxes.append((x, y, w, h, area))

    raw_boxes.sort(key=lambda item: (item[1], item[0], -item[4]))
    deduped: list[tuple[int, int, int, int]] = []
    for x, y, w, h, _ in raw_boxes:
        cx = x + w / 2.0
        cy = y + h / 2.0
        if any(
            abs(cx - (dx + dw / 2.0)) < 2.0 and abs(cy - (dy + dh / 2.0)) < 2.0
            for dx, dy, dw, dh in deduped
        ):
            continue
        deduped.append((x, y, w, h))
    return deduped


def detect_color_answer_area(image: np.ndarray) -> tuple[int, int, int, int] | None:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (95, 20, 150), (105, 255, 255))
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = []
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if area > 3000 and y > image.shape[0] * 0.2:
            components.append((area, x, y, w, h))
    if not components:
        return None
    _, x, y, w, h = max(components)
    return int(x), int(y), int(w), int(h)


def detect_structured_answer_area(image: np.ndarray) -> tuple[int, int, int, int] | None:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    threshold = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10
    )
    vertical = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(25, image.shape[0] // 30))),
    )
    horizontal = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(25, image.shape[1] // 20), 1)),
    )

    vertical_components: list[tuple[int, int, int, int, int]] = []
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(vertical)
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if h >= image.shape[0] * 0.18 and y >= image.shape[0] * 0.25:
            vertical_components.append((int(x), int(y), int(w), int(h), int(area)))
    if len(vertical_components) < 2:
        return None

    horizontal_components: list[tuple[int, int, int, int, int]] = []
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(horizontal)
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if w >= image.shape[1] * 0.14 and y >= image.shape[0] * 0.25:
            horizontal_components.append((int(x), int(y), int(w), int(h), int(area)))

    left = min(component[0] for component in vertical_components)
    right = max(component[0] + component[2] for component in vertical_components)
    top = min(component[1] for component in vertical_components)
    bottom = max(component[1] + component[3] for component in vertical_components)

    if horizontal_components:
        top = min(top, min(component[1] for component in horizontal_components))
        bottom = max(bottom, max(component[1] + component[3] for component in horizontal_components))

    width = right - left
    height = bottom - top
    if width < image.shape[1] * 0.35 or height < image.shape[0] * 0.2:
        return None
    return int(left), int(top), int(width), int(height)


def detect_answer_area(image: np.ndarray) -> tuple[int, int, int, int]:
    color_area = detect_color_answer_area(image)
    if color_area is not None:
        return color_area
    structured_area = detect_structured_answer_area(image)
    if structured_area is not None:
        return structured_area
    raise TemplateValidationError("Could not locate the answer area")


def _infer_centers_from_cluster(cluster: list[float], expected_count: int) -> list[float]:
    if len(cluster) >= expected_count:
        return [float(value) for value in sorted(cluster)[:expected_count]]
    if len(cluster) == 1:
        step = 17.0
        start = cluster[0] - step * (expected_count - 1) / 2.0
        return [float(start + step * index) for index in range(expected_count)]
    step = float(np.median(np.diff(sorted(cluster))))
    while len(cluster) < expected_count:
        if cluster[0] - step > 0:
            cluster = [cluster[0] - step] + cluster
        if len(cluster) < expected_count:
            cluster = cluster + [cluster[-1] + step]
    return [float(value) for value in sorted(cluster)[:expected_count]]


def _select_option_centers_from_clusters(
    clusters: list[list[float]], expected_count: int
) -> list[float]:
    if not clusters:
        raise TemplateValidationError("Could not infer option centers from an empty column")
    if len(clusters) <= expected_count:
        means = [float(np.mean(cluster)) for cluster in clusters]
        return _infer_centers_from_cluster(means, expected_count)

    cluster_means = [float(np.mean(cluster)) for cluster in clusters]
    cluster_counts = [len(cluster) for cluster in clusters]
    best_score = float("-inf")
    best_window: list[float] | None = None

    for start_index in range(0, len(cluster_means) - expected_count + 1):
        window_means = cluster_means[start_index : start_index + expected_count]
        window_counts = cluster_counts[start_index : start_index + expected_count]
        gaps = np.diff(window_means)
        gap_std = float(np.std(gaps)) if len(gaps) else 0.0
        count_sum = float(sum(window_counts))
        score = (count_sum * 10.0) - (gap_std * 8.0)
        if score > best_score:
            best_score = score
            best_window = window_means

    if best_window is None:
        raise TemplateValidationError("Could not select option centers from candidate clusters")
    return list(best_window)


def build_template_from_reference(
    reference_path: str | Path,
    questions: int,
    columns: int,
    options: int,
    *,
    template_id: str = "answer_sheet_v1",
    column_order: str = "ltr",
    option_order: str = "ltr",
    column_question_counts: list[int] | None = None,
) -> Template:
    if column_question_counts is not None:
        if len(column_question_counts) != columns:
            raise TemplateValidationError(
                f"Expected {columns} column question counts, got {len(column_question_counts)}"
            )
        if any(count < 0 for count in column_question_counts):
            raise TemplateValidationError("Column question counts must be non-negative")
        if sum(column_question_counts) != questions:
            raise TemplateValidationError(
                f"Column question counts must sum to {questions}, got {sum(column_question_counts)}"
            )

    image = load_image(reference_path)
    answer_x, answer_y, answer_w, answer_h = detect_answer_area(image)
    boxes = detect_cyan_bubble_boxes(image)
    if len(boxes) < questions * options * 0.7:
        boxes = detect_dark_bubble_boxes(image, (answer_x, answer_y, answer_w, answer_h))
    if len(boxes) < max(questions * options * 0.5, options * columns * 3):
        raise TemplateValidationError(
            f"Could not detect enough bubble outlines in {reference_path}; found {len(boxes)}"
        )

    centers = [
        (x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0)
        for x, y, w, h in boxes
        if answer_x <= x <= answer_x + answer_w and answer_y <= y <= answer_y + answer_h
    ]
    y_clusters = _cluster_sorted([center[1] for center in centers], tolerance=4.5)
    row_centers = [
        float(np.mean(cluster))
        for cluster in y_clusters
        if answer_y + 4 <= float(np.mean(cluster)) <= answer_y + answer_h - 4
    ]
    if not row_centers:
        raise TemplateValidationError("Could not infer answer rows from detected bubbles")

    column_width = answer_w / columns
    physical_groups: list[list[float]] = []
    for column_index in range(columns):
        start = answer_x + column_index * column_width
        end = answer_x + (column_index + 1) * column_width
        column_centers = [center[0] for center in centers if start <= center[0] < end]
        x_clusters = _cluster_sorted(column_centers, tolerance=6.0)
        x_values = _select_option_centers_from_clusters(x_clusters, options)
        x_values = sorted(x_values, reverse=(option_order == "rtl"))
        physical_groups.append(x_values)

    lookup: dict[tuple[int, int, int], tuple[float, float, float, float]] = {}
    lookup_distance: dict[tuple[int, int, int], float] = {}
    for cx, cy, rx, ry in centers:
        row_index = int(np.argmin([abs(cy - row_center) for row_center in row_centers]))
        column_index = int(min(columns - 1, max(0, (cx - answer_x) // column_width)))
        option_index = int(
            np.argmin([abs(cx - x_center) for x_center in physical_groups[int(column_index)]])
        )
        key = (row_index, int(column_index), option_index)
        target_x = physical_groups[int(column_index)][option_index]
        target_y = row_centers[row_index]
        distance = float(np.hypot(cx - target_x, cy - target_y))
        if key not in lookup_distance or distance < lookup_distance[key]:
            lookup[key] = (cx, cy, rx, ry)
            lookup_distance[key] = distance

    bubbles: dict[str, list[Bubble]] = {}
    question_number = 1
    median_rx = float(np.median([center[2] for center in centers]))
    median_ry = float(np.median([center[3] for center in centers]))
    ordered_column_indices = list(range(columns))
    if column_order == "rtl":
        ordered_column_indices = list(reversed(ordered_column_indices))

    per_column_limits = {index: len(row_centers) for index in range(columns)}
    if column_question_counts is not None:
        for physical_column_index, count in zip(ordered_column_indices, column_question_counts):
            per_column_limits[physical_column_index] = count

    for physical_column_index in ordered_column_indices:
        column_group = physical_groups[physical_column_index]
        for row_index in range(per_column_limits[physical_column_index]):
            if question_number > questions:
                break
            question_bubbles: list[Bubble] = []
            for option_index, x_center in enumerate(column_group):
                key = (row_index, physical_column_index, option_index)
                if key in lookup:
                    cx, cy, rx, ry = lookup[key]
                else:
                    cx, cy, rx, ry = (
                        x_center,
                        row_centers[row_index],
                        median_rx,
                        median_ry,
                    )
                question_bubbles.append(
                    Bubble(option=option_index + 1, cx=cx, cy=cy, rx=rx, ry=ry)
                )
            bubbles[str(question_number)] = question_bubbles
            question_number += 1
        if question_number > questions:
            break

    if len(bubbles) != questions:
        raise TemplateValidationError(
            f"Detected template capacity was insufficient for {questions} questions; created {len(bubbles)}"
        )

    marker_points, _ = detect_corner_markers(image, AlignmentParams())
    reference_points = []
    names = ["top_left", "top_right", "bottom_right", "bottom_left"]
    for name, (x, y) in zip(names, marker_points):
        reference_points.append(ReferencePoint(name=name, x=x, y=y))

    return Template(
        template_id=template_id,
        reference_size=ReferenceSize(width=image.shape[1], height=image.shape[0]),
        question_count=questions,
        option_count=options,
        alignment=TemplateAlignment(reference_points=reference_points),
        bubbles=bubbles,
        metadata={
            "source_reference": str(reference_path),
            "columns": columns,
            "column_order": column_order,
            "option_order": option_order,
            "detected_row_capacity": len(row_centers),
        },
    )
