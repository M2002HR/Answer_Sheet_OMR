from omr_reader.analyzer import analyze_sheet
from omr_reader.models import Bubble, ReferencePoint, ReferenceSize, Template, TemplateAlignment
from omr_reader.template_io import save_template


def test_analyzer_smoke_with_identity_alignment(tmp_path) -> None:
    template = Template(
        template_id="smoke",
        reference_size=ReferenceSize(width=717, height=991),
        question_count=2,
        option_count=4,
        alignment=TemplateAlignment(reference_points=[]),
        bubbles={
            "1": [
                Bubble(option=1, cx=100, cy=305, rx=10, ry=6),
                Bubble(option=2, cx=123, cy=305, rx=10, ry=6),
                Bubble(option=3, cx=146, cy=305, rx=10, ry=6),
                Bubble(option=4, cx=169, cy=305, rx=10, ry=6),
            ],
            "2": [
                Bubble(option=1, cx=100, cy=320, rx=10, ry=6),
                Bubble(option=2, cx=123, cy=320, rx=10, ry=6),
                Bubble(option=3, cx=146, cy=320, rx=10, ry=6),
                Bubble(option=4, cx=169, cy=320, rx=10, ry=6),
            ],
        },
    )
    template_path = tmp_path / "smoke_template.json"
    save_template(template_path, template)
    result = analyze_sheet("samples/scans/sample_sheet.png", template_path)
    assert result.meta.question_count == 2
    assert len(result.answers) == 2
    for answer in result.answers.values():
        assert len(answer.scores) == 4
