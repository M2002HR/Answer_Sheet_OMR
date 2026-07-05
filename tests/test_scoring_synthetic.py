import cv2
import numpy as np

from omr_reader.models import Bubble, ScoringParams
from omr_reader.scoring import score_bubble


BLUE = (255, 200, 0)


def make_canvas() -> np.ndarray:
    return np.full((80, 160, 3), 255, dtype=np.uint8)


def draw_bubble(canvas: np.ndarray, center: tuple[int, int], mark: str) -> Bubble:
    rx, ry = 18, 10
    cv2.ellipse(canvas, center, (rx, ry), 0, 0, 360, BLUE, 2)
    if mark == "filled":
        cv2.ellipse(canvas, center, (10, 6), 0, 0, 360, (10, 10, 10), -1)
    elif mark == "faint":
        cv2.ellipse(canvas, center, (10, 6), 0, 0, 360, (170, 170, 170), -1)
    elif mark == "noise":
        for offset in [(-7, 0), (6, 3), (2, -4)]:
            point = (center[0] + offset[0], center[1] + offset[1])
            cv2.circle(canvas, point, 1, (20, 20, 20), -1)
    return Bubble(option=1, cx=center[0], cy=center[1], rx=rx, ry=ry)


def test_blue_outline_is_not_counted_as_mark() -> None:
    canvas = make_canvas()
    bubble = draw_bubble(canvas, (40, 40), mark="empty")
    result = score_bubble(canvas, bubble, ScoringParams())
    assert result.score < 0.08


def test_dark_mark_scores_high() -> None:
    canvas = make_canvas()
    bubble = draw_bubble(canvas, (40, 40), mark="filled")
    result = score_bubble(canvas, bubble, ScoringParams())
    assert result.score > 0.35
    assert result.strong_dark_ratio > 0.10


def test_faint_mark_is_between_blank_and_full() -> None:
    empty_canvas = make_canvas()
    empty_bubble = draw_bubble(empty_canvas, (40, 40), mark="empty")
    faint_canvas = make_canvas()
    faint_bubble = draw_bubble(faint_canvas, (40, 40), mark="faint")
    filled_canvas = make_canvas()
    filled_bubble = draw_bubble(filled_canvas, (40, 40), mark="filled")

    blank = score_bubble(empty_canvas, empty_bubble, ScoringParams())
    faint = score_bubble(faint_canvas, faint_bubble, ScoringParams())
    filled = score_bubble(filled_canvas, filled_bubble, ScoringParams())
    assert blank.score < faint.score < filled.score
    assert faint.strong_dark_ratio < 0.08


def test_noise_does_not_trigger_strong_mark() -> None:
    canvas = make_canvas()
    bubble = draw_bubble(canvas, (40, 40), mark="noise")
    result = score_bubble(canvas, bubble, ScoringParams())
    assert result.score < 0.20
    assert result.strong_dark_ratio < 0.08
