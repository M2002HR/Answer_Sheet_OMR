from __future__ import annotations

import json
from pathlib import Path

from .exceptions import TemplateValidationError
from .models import Template


def load_template(path: str | Path) -> Template:
    template_path = Path(path)
    try:
        data = json.loads(template_path.read_text(encoding="utf-8"))
        return Template.model_validate(data)
    except Exception as exc:  # pragma: no cover - defensive rewrap
        raise TemplateValidationError(f"Invalid template file {template_path}: {exc}") from exc


def save_template(path: str | Path, template: Template) -> None:
    template_path = Path(path)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(
        json.dumps(template.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
