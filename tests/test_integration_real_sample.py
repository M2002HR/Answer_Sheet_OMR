from omr_reader.analyzer import analyze_sheet
from omr_reader.grading import grade_analysis_result, load_answer_key


def test_real_sample_grading_matches_expected_summary() -> None:
    result = analyze_sheet(
        "assets/sample_sheet.png",
        "templates/answer_sheet_template.json",
    )
    grading = grade_analysis_result(
        result,
        load_answer_key("assets/answer_key.json"),
        "assets/answer_key.json",
    )
    assert result.summary == {
        "single": 294,
        "blank": 6,
        "multiple": 0,
        "uncertain": 0,
        "needs_review": 0,
    }
    assert grading.summary.correct == 294
    assert grading.summary.wrong == 0
    assert grading.summary.blank == 6
    assert grading.summary.multiple == 0
    assert grading.summary.uncertain == 0


def test_real_sample_question_ordering_examples() -> None:
    grading = grade_analysis_result(
        analyze_sheet("assets/sample_sheet.png", "templates/answer_sheet_template.json"),
        load_answer_key("assets/answer_key.json"),
        "assets/answer_key.json",
    )
    assert grading.questions["1"].detected_selected == [1]
    assert grading.questions["51"].detected_selected == [4]
    assert grading.questions["101"].detected_selected == [4]
    assert grading.questions["251"].detected_selected == [2]
