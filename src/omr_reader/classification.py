from __future__ import annotations

from statistics import mean

from .models import (
    AlignmentStatus,
    BubbleScore,
    ClassificationParams,
    QuestionResult,
)


def _has_mark_evidence(score: BubbleScore, params: ClassificationParams) -> bool:
    return (
        score.strong_dark_ratio >= params.strong_dark_min
        or (score.component_area_ratio or 0.0) >= params.component_area_min
        or (
            score.mean_darkness >= params.marked_mean_darkness_min
            and score.ink_ratio >= params.marked_ink_ratio_min
        )
    )


def bubble_state(score: BubbleScore, params: ClassificationParams) -> str:
    if score.score >= params.marked_threshold and _has_mark_evidence(score, params):
        return "candidate_marked"
    if score.score >= params.faint_threshold:
        return "faint_trace_or_erased"
    return "empty"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _is_ambiguous_runner_up(score: BubbleScore, params: ClassificationParams) -> bool:
    near_mark_band = score.score >= max(
        params.faint_threshold,
        params.marked_threshold - params.uncertain_margin * 0.25,
    )
    if not near_mark_band:
        return False

    return (
        score.strong_dark_ratio >= params.strong_dark_min * 0.75
        or (score.component_area_ratio or 0.0) >= params.component_area_min * 0.75
        or (
            score.mean_darkness >= params.marked_mean_darkness_min
            and score.ink_ratio >= params.marked_ink_ratio_min * 0.75
        )
    )


def classify_question(
    question_id: int,
    scores: list[BubbleScore],
    params: ClassificationParams,
    alignment_status: AlignmentStatus = "ok",
) -> QuestionResult:
    if alignment_status == "failed":
        return QuestionResult(
            status="uncertain",
            selected=[],
            confidence=0.0,
            warnings=["alignment_failed"],
            scores={str(score.option): round(score.score, 4) for score in scores},
            bubble_evidence={str(score.option): score.evidence() for score in scores},
        )

    for score in scores:
        score.state = bubble_state(score, params)
        score.is_faint = score.state == "faint_trace_or_erased"
        score.is_strong = score.state == "candidate_marked"

    sorted_scores = sorted(scores, key=lambda item: item.score, reverse=True)
    marked = [score for score in sorted_scores if score.state == "candidate_marked"]
    faint = [score for score in sorted_scores if score.state == "faint_trace_or_erased"]
    warnings: list[str] = []
    if alignment_status == "low_confidence":
        warnings.append("alignment_low_confidence")

    if not marked:
        if faint:
            warnings.append("faint_trace_or_erased")
            confidence = _clamp(1.0 - max(score.score for score in faint))
        else:
            confidence = _clamp(1.0 - mean(score.score for score in scores))
        return QuestionResult(
            status="blank",
            selected=[],
            confidence=confidence,
            warnings=warnings,
            scores={str(score.option): round(score.score, 4) for score in sorted(scores, key=lambda item: item.option)},
            bubble_evidence={str(score.option): score.evidence() for score in sorted(scores, key=lambda item: item.option)},
        )

    if len(marked) == 1:
        top = marked[0]
        runner_up = sorted_scores[1] if len(sorted_scores) > 1 else None
        second = runner_up.score if runner_up is not None else 0.0
        margin = top.score - second
        if (
            runner_up is not None
            and margin < params.uncertain_margin
            and _is_ambiguous_runner_up(runner_up, params)
        ):
            warnings.append("low_margin")
            return QuestionResult(
                status="uncertain",
                selected=[top.option],
                confidence=_clamp(margin / max(params.uncertain_margin, 1e-6)),
                warnings=warnings,
                scores={str(score.option): round(score.score, 4) for score in sorted(scores, key=lambda item: item.option)},
                bubble_evidence={str(score.option): score.evidence() for score in sorted(scores, key=lambda item: item.option)},
            )
        threshold_gain = top.score - params.marked_threshold
        confidence = _clamp(0.55 + 0.8 * margin + threshold_gain)
        return QuestionResult(
            status="single",
            selected=[top.option],
            confidence=confidence,
            warnings=warnings,
            scores={str(score.option): round(score.score, 4) for score in sorted(scores, key=lambda item: item.option)},
            bubble_evidence={str(score.option): score.evidence() for score in sorted(scores, key=lambda item: item.option)},
        )

    if not params.allow_multiple_marks:
        top = marked[0]
        warnings.append("multiple_candidates_collapsed")
        confidence = _clamp(top.score)
        return QuestionResult(
            status="single",
            selected=[top.option],
            confidence=confidence,
            warnings=warnings,
            scores={str(score.option): round(score.score, 4) for score in sorted(scores, key=lambda item: item.option)},
            bubble_evidence={str(score.option): score.evidence() for score in sorted(scores, key=lambda item: item.option)},
        )

    warnings.append("multiple_marks")
    confidence = _clamp(mean(score.score for score in marked))
    return QuestionResult(
        status="multiple",
        selected=sorted(score.option for score in marked),
        confidence=confidence,
        warnings=warnings,
        scores={str(score.option): round(score.score, 4) for score in sorted(scores, key=lambda item: item.option)},
        bubble_evidence={str(score.option): score.evidence() for score in sorted(scores, key=lambda item: item.option)},
    )


def adapt_classification_params(
    scores: list[BubbleScore], params: ClassificationParams
) -> ClassificationParams:
    if not params.adaptive_thresholds or len(scores) < 40:
        return params

    sorted_values = sorted(score.score for score in scores)
    faint_anchor = sorted_values[int(len(sorted_values) * 0.60)]
    marked_anchor = sorted_values[int(len(sorted_values) * 0.92)]
    spread = max(0.03, marked_anchor - faint_anchor)
    faint = faint_anchor + spread * 0.15
    marked = faint_anchor + spread * 0.55

    adapted = params.model_copy(deep=True)
    adapted.faint_threshold = min(
        params.max_faint_threshold, max(params.min_faint_threshold, faint)
    )
    adapted.marked_threshold = min(
        params.max_marked_threshold, max(params.min_marked_threshold, marked)
    )
    return adapted
