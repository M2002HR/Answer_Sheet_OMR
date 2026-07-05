from omr_reader.config import load_config


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
