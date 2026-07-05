from omr_reader.alignment import detect_corner_markers
from omr_reader.models import AlignmentParams
from omr_reader.preprocess import load_image
from omr_reader.template_builder import build_template_from_reference

REFERENCE_SAMPLE = "samples/scans/202512061032_Page_01.png"


def test_detect_corner_markers_on_sample() -> None:
    image = load_image(REFERENCE_SAMPLE)
    points, diagnostics = detect_corner_markers(image, AlignmentParams())
    assert len(points) == 4
    assert diagnostics["method"] == "corner_contours"
    top_left, top_right, bottom_right, bottom_left = points
    assert top_left[0] < 80 and top_left[1] < 80
    assert top_right[0] > 500 and top_right[1] < 100
    assert bottom_right[0] > 500 and bottom_right[1] > 700
    assert bottom_left[0] < 80 and bottom_left[1] > 700


def test_build_template_on_sample() -> None:
    template = build_template_from_reference(
        REFERENCE_SAMPLE, questions=60, columns=3, options=4
    )
    assert template.question_count == 60
    assert template.option_count == 4
    assert len(template.bubbles) == 60
    assert template.bubbles["1"][0].cx < template.bubbles["60"][0].cx
    assert template.bubbles["1"][0].cy < template.bubbles["20"][0].cy
    assert template.bubbles["20"][0].cx == template.bubbles["1"][0].cx
    assert template.bubbles["21"][0].cx > template.bubbles["20"][0].cx
    assert template.bubbles["60"][0].cy > template.bubbles["41"][0].cy


def test_build_template_allows_partial_capacity() -> None:
    template = build_template_from_reference(
        REFERENCE_SAMPLE, questions=8, columns=3, options=4
    )
    assert template.question_count == 8
    assert len(template.bubbles) == 8
    assert abs(template.bubbles["1"][0].cx - template.bubbles["8"][0].cx) < 1.5
    assert template.bubbles["8"][0].cy > template.bubbles["1"][0].cy


def test_build_template_supports_explicit_column_distribution() -> None:
    template = build_template_from_reference(
        REFERENCE_SAMPLE,
        questions=8,
        columns=3,
        options=4,
        column_question_counts=[3, 3, 2],
    )
    assert abs(template.bubbles["1"][0].cx - template.bubbles["3"][0].cx) < 1.5
    assert template.bubbles["4"][0].cx > template.bubbles["3"][0].cx
    assert template.bubbles["7"][0].cx > template.bubbles["6"][0].cx
