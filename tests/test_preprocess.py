from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from omr_reader.models import PreprocessParams
from omr_reader.preprocess import enhance_contrast, load_image
from omr_reader.models import Bubble, ScoringParams
from omr_reader.scoring import score_bubble


def test_load_image_supports_pdf(tmp_path) -> None:
    image_path = tmp_path / "page.png"
    pdf_path = tmp_path / "page.pdf"
    Image.fromarray(np.full((40, 60, 3), 255, dtype=np.uint8)).save(image_path)
    Image.open(image_path).save(pdf_path, "PDF")

    rendered = load_image(pdf_path, pdf_dpi=120)
    assert rendered.shape[0] > 0
    assert rendered.shape[1] > 0


def test_enhance_contrast_raises_faint_mark_score() -> None:
    canvas = np.full((80, 160, 3), 255, dtype=np.uint8)
    bubble = Bubble(option=1, cx=40, cy=40, rx=18, ry=10)
    cv2.ellipse(canvas, (40, 40), (18, 10), 0, 0, 360, (120, 120, 120), 2)
    cv2.ellipse(canvas, (40, 40), (10, 6), 0, 0, 360, (180, 180, 180), -1)

    before = score_bubble(canvas, bubble, ScoringParams())
    enhanced = enhance_contrast(canvas, PreprocessParams())
    after = score_bubble(enhanced, bubble, ScoringParams())
    assert after.score > before.score
