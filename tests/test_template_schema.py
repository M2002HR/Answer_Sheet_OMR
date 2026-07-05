import json

import pytest

from omr_reader.exceptions import TemplateValidationError
from omr_reader.template_io import load_template, save_template
from omr_reader.models import Bubble, ReferenceSize, Template, TemplateAlignment


def test_template_roundtrip(tmp_path) -> None:
    template = Template(
        template_id="demo",
        reference_size=ReferenceSize(width=100, height=200),
        question_count=1,
        option_count=4,
        alignment=TemplateAlignment(reference_points=[]),
        bubbles={
            "1": [
                Bubble(option=1, cx=10, cy=20, rx=3, ry=2),
                Bubble(option=2, cx=20, cy=20, rx=3, ry=2),
                Bubble(option=3, cx=30, cy=20, rx=3, ry=2),
                Bubble(option=4, cx=40, cy=20, rx=3, ry=2),
            ]
        },
    )
    path = tmp_path / "template.json"
    save_template(path, template)
    loaded = load_template(path)
    assert loaded.template_id == "demo"
    assert loaded.bubbles["1"][0].option == 1


def test_invalid_template_raises(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "template_id": "bad",
                "reference_size": {"width": 100, "height": 200},
                "question_count": 1,
                "option_count": 4,
                "bubbles": {"1": [{"option": 1, "cx": 10, "cy": 10, "rx": 3, "ry": 3}]},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError):
        load_template(path)
