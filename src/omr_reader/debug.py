from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np

from .exceptions import OutputWriteError
from .models import AnalysisResult, Bubble, BubbleScore, QuestionResult, Template
from .preprocess import create_dark_ink_mask


STATUS_COLORS = {
    "single": (0, 180, 0),
    "blank": (140, 140, 140),
    "multiple": (0, 0, 220),
    "uncertain": (160, 0, 160),
}


def save_debug_artifacts(
    debug_dir: str | Path,
    aligned_image: np.ndarray,
    template: Template,
    bubble_scores: dict[str, list[BubbleScore]],
    answers: dict[str, QuestionResult],
    dark_pixel_threshold: int,
) -> None:
    output_dir = Path(debug_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_dir / "aligned.png"), aligned_image):
        raise OutputWriteError(f"Could not write {(output_dir / 'aligned.png')}")

    ink_mask = create_dark_ink_mask(aligned_image, dark_pixel_threshold=dark_pixel_threshold)
    if not cv2.imwrite(str(output_dir / "ink_mask.png"), ink_mask):
        raise OutputWriteError(f"Could not write {(output_dir / 'ink_mask.png')}")

    overlay = draw_bubbles_overlay(aligned_image, template, bubble_scores, answers)
    if not cv2.imwrite(str(output_dir / "bubbles_overlay.png"), overlay):
        raise OutputWriteError(f"Could not write {(output_dir / 'bubbles_overlay.png')}")

    scores_path = output_dir / "bubbles_scores.csv"
    with scores_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "question_id",
                "option",
                "cx",
                "cy",
                "score",
                "ink_ratio",
                "mean_darkness",
                "strong_dark_ratio",
                "component_area_ratio",
                "state",
            ]
        )
        for question_id, scores in bubble_scores.items():
            bubble_map = {bubble.option: bubble for bubble in template.bubbles[question_id]}
            for score in sorted(scores, key=lambda item: item.option):
                bubble = bubble_map[score.option]
                writer.writerow(
                    [
                        question_id,
                        score.option,
                        bubble.cx,
                        bubble.cy,
                        round(score.score, 6),
                        round(score.ink_ratio, 6),
                        round(score.mean_darkness, 6),
                        round(score.strong_dark_ratio, 6),
                        round(score.component_area_ratio or 0.0, 6),
                        score.state,
                    ]
                )

    review = {
        question_id: result.model_dump(mode="json")
        for question_id, result in answers.items()
        if result.status != "single"
        or any(
            warning
            in {
                "faint_trace_or_erased",
                "low_margin",
                "multiple_marks",
                "alignment_low_confidence",
                "alignment_failed",
            }
            for warning in result.warnings
        )
    }
    (output_dir / "questions_review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def draw_bubbles_overlay(
    aligned_image: np.ndarray,
    template: Template,
    bubble_scores: dict[str, list[BubbleScore]],
    answers: dict[str, QuestionResult],
) -> np.ndarray:
    canvas = aligned_image.copy()
    for question_id, bubbles in template.bubbles.items():
        question_result = answers[question_id]
        color = STATUS_COLORS[question_result.status]
        scores_for_question = {score.option: score for score in bubble_scores.get(question_id, [])}
        for bubble in bubbles:
            score = scores_for_question.get(bubble.option)
            thickness = 2 if bubble.option in question_result.selected else 1
            if score and score.state == "faint_trace_or_erased":
                outline = (0, 165, 255)
            elif score and score.state == "candidate_marked":
                outline = color
            else:
                outline = (180, 180, 180)
            center = (int(round(bubble.cx)), int(round(bubble.cy)))
            axes = (int(round(bubble.rx)), int(round(bubble.ry)))
            cv2.ellipse(canvas, center, axes, 0, 0, 360, outline, thickness)
    return canvas
