from omr_reader.config import apply_overrides, load_config


def test_load_yaml_config(tmp_path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
scoring:
  dark_pixel_threshold: 110
classification:
  marked_threshold: 0.25
  adaptive_thresholds: true
alignment:
  min_confidence: 0.8
""".strip(),
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.scoring.dark_pixel_threshold == 110
    assert config.classification.marked_threshold == 0.25
    assert config.classification.adaptive_thresholds is True
    assert config.alignment.min_confidence == 0.8


def test_apply_overrides_updates_thresholds() -> None:
    config = load_config(None)
    overridden = apply_overrides(
        config,
        {
            "classification": {"marked_threshold": 0.18, "allow_multiple_marks": True},
            "preprocess": {"clahe_clip_limit": 4.0},
            "scoring": {"dark_pixel_threshold": 135},
        },
    )
    assert overridden.classification.marked_threshold == 0.18
    assert overridden.classification.allow_multiple_marks is True
    assert overridden.preprocess.clahe_clip_limit == 4.0
    assert overridden.scoring.dark_pixel_threshold == 135
