from __future__ import annotations

import json
from pathlib import Path

from .exceptions import TemplateValidationError
from .models import (
    AnalysisResult,
    AnswerKey,
    GradedQuestionResult,
    GradingResult,
    GradingSummary,
)


LETTER_TO_OPTION = {"a": 1, "b": 2, "c": 3, "d": 4}


def load_answer_key(path: str | Path) -> AnswerKey:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    answers: dict[str, int] = {}
    for question_id, value in raw.items():
        normalized_question_id = str(int(question_id))
        if isinstance(value, str):
            option = LETTER_TO_OPTION.get(value.strip().lower())
        elif isinstance(value, int):
            option = value
        else:
            option = None
        if option is None or option < 1 or option > 4:
            raise TemplateValidationError(
                f"Invalid answer key entry for question {question_id}: {value!r}"
            )
        answers[normalized_question_id] = option
    return AnswerKey(answers=answers)


def grade_analysis_result(
    analysis_result: AnalysisResult, answer_key: AnswerKey, answer_key_path: str | Path
) -> GradingResult:
    analysis_questions = set(analysis_result.answers)
    key_questions = set(answer_key.answers)
    if analysis_questions != key_questions:
        missing_in_key = sorted(analysis_questions - key_questions, key=int)
        extra_in_key = sorted(key_questions - analysis_questions, key=int)
        raise TemplateValidationError(
            "Answer key questions do not match analysis questions. "
            f"Missing in key: {missing_in_key[:10]}; extra in key: {extra_in_key[:10]}"
        )

    graded_questions: dict[str, GradedQuestionResult] = {}
    correct = wrong = blank = multiple = uncertain = answered = 0

    for question_id, question_result in analysis_result.answers.items():
        expected = answer_key.answers.get(question_id)
        grading_status = "uncertain"
        is_correct = False

        if question_result.status == "single":
            answered += 1
            if expected is not None and question_result.selected == [expected]:
                grading_status = "correct"
                is_correct = True
                correct += 1
            else:
                grading_status = "wrong"
                wrong += 1
        elif question_result.status == "blank":
            grading_status = "blank"
            blank += 1
        elif question_result.status == "multiple":
            grading_status = "multiple"
            multiple += 1
        else:
            grading_status = "uncertain"
            uncertain += 1

        graded_questions[question_id] = GradedQuestionResult(
            question_id=int(question_id),
            expected=expected,
            detected_status=question_result.status,
            detected_selected=question_result.selected,
            grading_status=grading_status,
            is_correct=is_correct,
            warnings=list(question_result.warnings),
        )

    total_questions = len(analysis_result.answers)
    accuracy = correct / total_questions if total_questions else 0.0
    return GradingResult(
        meta={
            "answer_key_path": str(answer_key_path),
            "template_id": analysis_result.meta.template_id,
            "image_path": analysis_result.meta.image_path,
        },
        questions=graded_questions,
        summary=GradingSummary(
            total_questions=total_questions,
            answered=answered,
            correct=correct,
            wrong=wrong,
            blank=blank,
            multiple=multiple,
            uncertain=uncertain,
            accuracy=accuracy,
        ),
    )


def write_grading_result(path: str | Path, result: GradingResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
