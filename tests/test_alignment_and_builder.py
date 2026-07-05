from omr_reader.alignment import detect_corner_markers
from omr_reader.models import AlignmentParams
from omr_reader.preprocess import load_image
from omr_reader.template_builder import build_template_from_reference


def test_detect_corner_markers_on_sample() -> None:
    image = load_image("assets/sample_sheet.png")
    points, diagnostics = detect_corner_markers(image, AlignmentParams())
    assert len(points) == 4
    assert diagnostics["method"] == "corner_contours"
    top_left, top_right, bottom_right, bottom_left = points
    assert top_left[0] < 80 and top_left[1] < 80
    assert top_right[0] > 630 and top_right[1] < 80
    assert bottom_right[0] > 630 and bottom_right[1] > 930
    assert bottom_left[0] < 80 and bottom_left[1] > 930


def test_build_template_on_sample() -> None:
    template = build_template_from_reference(
        "assets/sample_sheet.png", questions=300, columns=6, options=4
    )
    assert template.question_count == 300
    assert template.option_count == 4
    assert len(template.bubbles) == 300
    assert template.bubbles["1"][0].cx > template.bubbles["300"][0].cx
