import json

import pytest

from omr_reader.grading import grade_analysis_result, load_answer_key
from omr_reader.models import (
    AlignmentResultMeta,
    AnalysisMeta,
    AnalysisResult,
    AnswerKey,
    QuestionResult,
)
from omr_reader.exceptions import TemplateValidationError


def make_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        meta=AnalysisMeta(
            image_path="sample.png",
            template_id="t1",
            question_count=4,
            option_count=4,
            alignment=AlignmentResultMeta(status="ok", confidence=1.0, method="test"),
            thresholds={"marked_threshold": 0.22, "faint_threshold": 0.1, "uncertain_margin": 0.07},
        ),
        answers={
            "1": QuestionResult(status="single", selected=[1], confidence=1.0, scores={"1": 0.8, "2": 0.1, "3": 0.0, "4": 0.0}),
            "2": QuestionResult(status="single", selected=[3], confidence=1.0, scores={"1": 0.0, "2": 0.0, "3": 0.8, "4": 0.0}),
            "3": QuestionResult(status="blank", selected=[], confidence=1.0, scores={"1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0}),
            "4": QuestionResult(status="multiple", selected=[2, 4], confidence=1.0, scores={"1": 0.0, "2": 0.7, "3": 0.0, "4": 0.7}),
        },
        summary={"single": 2, "blank": 1, "multiple": 1, "uncertain": 0, "needs_review": 1},
    )


def test_grade_analysis_result_counts() -> None:
    analysis = make_analysis_result()
    answer_key = load_answer_key_from_mapping({"1": "a", "2": "b", "3": "c", "4": "d"})
    graded = grade_analysis_result(analysis, answer_key, "answer_key.json")
    assert graded.summary.correct == 1
    assert graded.summary.wrong == 1
    assert graded.summary.blank == 1
    assert graded.summary.multiple == 1
    assert graded.questions["1"].grading_status == "correct"
    assert graded.questions["2"].grading_status == "wrong"


def test_grade_analysis_result_requires_matching_questions() -> None:
    analysis = make_analysis_result()
    answer_key = load_answer_key_from_mapping({"1": "a", "2": "b"})
    with pytest.raises(TemplateValidationError):
        grade_analysis_result(analysis, answer_key, "answer_key.json")


def test_load_answer_key_letters(tmp_path) -> None:
    path = tmp_path / "answer_key.json"
    path.write_text(json.dumps({"1": "a", "2": "D"}), encoding="utf-8")
    key = load_answer_key(path)
    assert key.answers == {"1": 1, "2": 4}


def load_answer_key_from_mapping(mapping: dict[str, str]):
    return AnswerKey(
        answers={str(k): {"a": 1, "b": 2, "c": 3, "d": 4}[v.lower()] for k, v in mapping.items()}
    )
