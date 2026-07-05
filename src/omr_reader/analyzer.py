from __future__ import annotations

import json
from pathlib import Path

from .alignment import align_sheet
from .classification import adapt_classification_params, classify_question
from .config import load_config
from .debug import save_debug_artifacts
from .models import (
    AlignedSheet,
    AlignmentResultMeta,
    AnalysisMeta,
    AnalysisResult,
    BubbleScore,
    OMRConfig,
    QuestionResult,
    Template,
)
from .preprocess import load_image, normalize_image, remove_shadows_or_normalize_illumination
from .scoring import score_question_bubbles
from .template_io import load_template


def _thresholds_dict(config: OMRConfig) -> dict[str, float]:
    return {
        "marked_threshold": config.classification.marked_threshold,
        "faint_threshold": config.classification.faint_threshold,
        "uncertain_margin": config.classification.uncertain_margin,
        "strong_dark_min": config.classification.strong_dark_min,
    }


def summarize_answers(
    answers: dict[str, QuestionResult], alignment_status: str
) -> dict[str, int]:
    summary = {"single": 0, "blank": 0, "multiple": 0, "uncertain": 0, "needs_review": 0}
    for result in answers.values():
        summary[result.status] += 1
        needs_review = (
            result.status in {"multiple", "uncertain"}
            or "faint_trace_or_erased" in result.warnings
            or "low_margin" in result.warnings
            or alignment_status != "ok"
        )
        if needs_review:
            summary["needs_review"] += 1
    return summary


def _fallback_uncertain_answers(template: Template, warning: str) -> dict[str, QuestionResult]:
    answers: dict[str, QuestionResult] = {}
    for question_id, bubbles in template.bubbles.items():
        zero_scores = {str(bubble.option): 0.0 for bubble in bubbles}
        answers[question_id] = QuestionResult(
            status="uncertain",
            selected=[],
            confidence=0.0,
            warnings=[warning],
            scores=zero_scores,
            bubble_evidence=None,
        )
    return answers


def analyze_sheet(
    image_path: str | Path,
    template_path: str | Path,
    config_path: str | Path | None = None,
    debug_dir: str | Path | None = None,
) -> AnalysisResult:
    config = load_config(config_path)
    template = load_template(template_path)
    image = load_image(image_path)
    normalized = normalize_image(image)
    preprocessed = remove_shadows_or_normalize_illumination(normalized)
    aligned = align_sheet(preprocessed, template, config.alignment)
    errors: list[str] = []

    if aligned.status == "failed":
        answers = _fallback_uncertain_answers(template, "alignment_failed")
        result = AnalysisResult(
            meta=AnalysisMeta(
                image_path=str(image_path),
                template_id=template.template_id,
                question_count=template.question_count,
                option_count=template.option_count,
                alignment=AlignmentResultMeta(
                    status=aligned.status,
                    confidence=aligned.confidence,
                    method=aligned.method,
                    diagnostics=aligned.diagnostics,
                ),
                thresholds=_thresholds_dict(config),
                errors=["alignment_failed"],
            ),
            answers=answers,
            summary=summarize_answers(answers, aligned.status),
        )
        if debug_dir is not None:
            save_debug_artifacts(
                debug_dir,
                aligned.image,
                template,
                {question_id: [] for question_id in template.bubbles},
                answers,
                config.scoring.dark_pixel_threshold,
            )
        return result

    bubble_scores: dict[str, list[BubbleScore]] = {}
    all_scores: list[BubbleScore] = []
    for question_id, bubbles in template.bubbles.items():
        scores = score_question_bubbles(aligned.image, bubbles, config.scoring)
        bubble_scores[question_id] = scores
        all_scores.extend(scores)

    active_classification = adapt_classification_params(all_scores, config.classification)
    answers: dict[str, QuestionResult] = {}
    for question_id, scores in bubble_scores.items():
        answers[question_id] = classify_question(
            int(question_id), scores, active_classification, alignment_status=aligned.status
        )

    effective_config = config.model_copy(deep=True)
    effective_config.classification = active_classification
    result = AnalysisResult(
        meta=AnalysisMeta(
            image_path=str(image_path),
            template_id=template.template_id,
            question_count=template.question_count,
            option_count=template.option_count,
            alignment=AlignmentResultMeta(
                status=aligned.status,
                confidence=aligned.confidence,
                method=aligned.method,
                diagnostics=aligned.diagnostics,
            ),
            thresholds=_thresholds_dict(effective_config),
            errors=errors,
        ),
        answers=answers,
        summary=summarize_answers(answers, aligned.status),
    )

    if debug_dir is not None:
        save_debug_artifacts(
            debug_dir,
            aligned.image,
            template,
            bubble_scores,
            answers,
            config.scoring.dark_pixel_threshold,
        )
    return result


def write_analysis_result(path: str | Path, result: AnalysisResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
