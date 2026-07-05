from omr_reader.classification import adapt_classification_params, classify_question
from omr_reader.models import BubbleScore, ClassificationParams


def score(option: int, value: float, strong: float | None = None) -> BubbleScore:
    strong_ratio = value if strong is None else strong
    return BubbleScore(
        option=option,
        score=value,
        ink_ratio=value,
        mean_darkness=value,
        strong_dark_ratio=strong_ratio,
        component_area_ratio=value,
    )


def test_single_mark_classification() -> None:
    params = ClassificationParams()
    result = classify_question(
        1,
        [score(1, 0.80), score(2, 0.02), score(3, 0.03), score(4, 0.04)],
        params,
    )
    assert result.status == "single"
    assert result.selected == [1]


def test_blank_classification() -> None:
    params = ClassificationParams()
    result = classify_question(
        1,
        [score(1, 0.02, 0.01), score(2, 0.03, 0.01), score(3, 0.01, 0.0), score(4, 0.04, 0.01)],
        params,
    )
    assert result.status == "blank"
    assert result.selected == []


def test_faint_trace_classification() -> None:
    params = ClassificationParams()
    result = classify_question(
        2,
        [score(1, 0.12, 0.01), score(2, 0.03, 0.01), score(3, 0.02, 0.0), score(4, 0.04, 0.0)],
        params,
    )
    assert result.status == "blank"
    assert "faint_trace_or_erased" in result.warnings


def test_multiple_marks_classification() -> None:
    params = ClassificationParams()
    result = classify_question(
        3,
        [score(1, 0.70), score(2, 0.03), score(3, 0.68), score(4, 0.02)],
        params,
    )
    assert result.status == "multiple"
    assert result.selected == [1, 3]
    assert "multiple_marks" in result.warnings


def test_low_margin_goes_uncertain() -> None:
    params = ClassificationParams()
    result = classify_question(
        4,
        [score(1, 0.23), score(2, 0.19), score(3, 0.03, 0.01), score(4, 0.02, 0.01)],
        params,
    )
    assert result.status == "uncertain"
    assert "low_margin" in result.warnings


def test_failed_alignment_forces_uncertain() -> None:
    params = ClassificationParams()
    result = classify_question(
        5,
        [score(1, 0.80), score(2, 0.02), score(3, 0.03), score(4, 0.04)],
        params,
        alignment_status="failed",
    )
    assert result.status == "uncertain"
    assert result.warnings == ["alignment_failed"]


def test_adaptive_thresholds_stay_in_safe_range() -> None:
    params = ClassificationParams(adaptive_thresholds=True)
    scores = [
        score(index % 4 + 1, value)
        for index, value in enumerate([0.01] * 80 + [0.08] * 20 + [0.35] * 10 + [0.7] * 10)
    ]
    adapted = adapt_classification_params(scores, params)
    assert params.min_faint_threshold <= adapted.faint_threshold <= params.max_faint_threshold
    assert params.min_marked_threshold <= adapted.marked_threshold <= params.max_marked_threshold
