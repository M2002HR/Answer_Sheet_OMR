from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .models import OMRConfig


def default_config() -> OMRConfig:
    return OMRConfig()


def load_config(config_path: str | Path | None) -> OMRConfig:
    if config_path is None:
        return default_config()
    path = Path(config_path)
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text) or {}
    else:
        data = json.loads(raw_text)
    return OMRConfig.model_validate(data)
