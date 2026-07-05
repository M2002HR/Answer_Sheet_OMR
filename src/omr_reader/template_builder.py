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


def detect_answer_area(image: np.ndarray) -> tuple[int, int, int, int]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (95, 20, 150), (105, 255, 255))
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = []
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if area > 3000 and y > image.shape[0] * 0.2:
            components.append((area, x, y, w, h))
    if not components:
        raise TemplateValidationError("Could not locate the cyan answer area")
    _, x, y, w, h = max(components)
    return int(x), int(y), int(w), int(h)


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


def build_template_from_reference(
    reference_path: str | Path,
    questions: int,
    columns: int,
    options: int,
    *,
    template_id: str = "answer_sheet_v1",
    column_order: str = "rtl",
    option_order: str = "ltr",
) -> Template:
    if questions % columns != 0:
        raise TemplateValidationError(
            f"Question count {questions} must be divisible by columns {columns}"
        )
    image = load_image(reference_path)
    answer_x, answer_y, answer_w, answer_h = detect_answer_area(image)
    boxes = detect_cyan_bubble_boxes(image)
    if len(boxes) < questions * options * 0.7:
        raise TemplateValidationError(
            f"Could not detect enough bubble outlines in {reference_path}; found {len(boxes)}"
        )

    centers = [
        (x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0)
        for x, y, w, h in boxes
        if answer_x <= x <= answer_x + answer_w and answer_y <= y <= answer_y + answer_h
    ]
    y_clusters = _cluster_sorted([center[1] for center in centers], tolerance=4.5)
    row_centers = [float(np.mean(cluster)) for cluster in y_clusters]
    rows_per_column = questions // columns
    if len(row_centers) < rows_per_column:
        raise TemplateValidationError(
            f"Expected at least {rows_per_column} answer rows, found {len(row_centers)}"
        )
    row_centers = row_centers[:rows_per_column]

    column_width = answer_w / columns
    physical_groups: list[list[float]] = []
    for column_index in range(columns):
        start = answer_x + column_index * column_width
        end = answer_x + (column_index + 1) * column_width
        column_centers = [center[0] for center in centers if start <= center[0] < end]
        x_clusters = _cluster_sorted(column_centers, tolerance=6.0)
        x_values = [float(np.mean(cluster)) for cluster in x_clusters]
        x_values = _infer_centers_from_cluster(x_values, options)
        x_values = sorted(x_values, reverse=(option_order == "rtl"))
        physical_groups.append(x_values)

    lookup: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    for cx, cy, rx, ry in centers:
        row_index = int(np.argmin([abs(cy - row_center) for row_center in row_centers]))
        column_index = int(min(columns - 1, max(0, (cx - answer_x) // column_width)))
        option_index = int(
            np.argmin([abs(cx - x_center) for x_center in physical_groups[int(column_index)]])
        )
        key = (row_index, int(column_index), option_index)
        lookup[key] = (cx, cy, rx, ry)

    bubbles: dict[str, list[Bubble]] = {}
    question_number = 1
    median_rx = float(np.median([center[2] for center in centers]))
    median_ry = float(np.median([center[3] for center in centers]))
    ordered_column_indices = list(range(columns))
    if column_order == "rtl":
        ordered_column_indices = list(reversed(ordered_column_indices))

    for physical_column_index in ordered_column_indices:
        column_group = physical_groups[physical_column_index]
        for row_index in range(rows_per_column):
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
        },
    )
