from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator

QuestionStatus = Literal["single", "blank", "multiple", "uncertain"]
AlignmentStatus = Literal["ok", "low_confidence", "failed"]
GradeStatus = Literal["correct", "wrong", "blank", "multiple", "uncertain"]


class ReferenceSize(BaseModel):
    width: int
    height: int


class ReferencePoint(BaseModel):
    name: str
    x: float
    y: float


class Bubble(BaseModel):
    option: int
    cx: float
    cy: float
    rx: float
    ry: float


class TemplateAlignment(BaseModel):
    reference_points: list[ReferencePoint] = Field(default_factory=list)


class Template(BaseModel):
    template_id: str
    version: str = "1.0.0"
    reference_size: ReferenceSize
    question_count: int
    option_count: int
    alignment: TemplateAlignment = Field(default_factory=TemplateAlignment)
    bubbles: dict[str, list[Bubble]]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bubbles(self) -> "Template":
        if len(self.bubbles) != self.question_count:
            raise ValueError(
                f"Template question count mismatch: expected {self.question_count}, found {len(self.bubbles)}"
            )
        for question_id, bubbles in self.bubbles.items():
            if len(bubbles) != self.option_count:
                raise ValueError(
                    f"Question {question_id} has {len(bubbles)} bubbles, expected {self.option_count}"
                )
            options = sorted(bubble.option for bubble in bubbles)
            expected = list(range(1, self.option_count + 1))
            if options != expected:
                raise ValueError(
                    f"Question {question_id} options are {options}, expected {expected}"
                )
        return self


class ScoreWeights(BaseModel):
    ink_ratio: float = 0.45
    mean_darkness: float = 0.30
    strong_dark_ratio: float = 0.25
    component_area_ratio: float = 0.0

    def normalized_items(self) -> list[tuple[str, float]]:
        weights = [
            ("ink_ratio", self.ink_ratio),
            ("mean_darkness", self.mean_darkness),
            ("strong_dark_ratio", self.strong_dark_ratio),
            ("component_area_ratio", self.component_area_ratio),
        ]
        total = sum(value for _, value in weights)
        if total <= 0:
            return [(name, 0.0) for name, _ in weights]
        return [(name, value / total) for name, value in weights]


class ScoringParams(BaseModel):
    inner_rx_scale: float = 0.62
    inner_ry_scale: float = 0.62
    dark_pixel_threshold: int = 120
    strong_dark_threshold: int = 80
    min_component_pixels: int = 4
    weights: ScoreWeights = Field(default_factory=ScoreWeights)


class ClassificationParams(BaseModel):
    faint_threshold: float = 0.10
    marked_threshold: float = 0.20
    strong_dark_min: float = 0.08
    component_area_min: float = 0.01
    uncertain_margin: float = 0.07
    adaptive_thresholds: bool = False
    min_marked_threshold: float = 0.18
    max_marked_threshold: float = 0.32
    min_faint_threshold: float = 0.06
    max_faint_threshold: float = 0.14


class PreprocessParams(BaseModel):
    normalize_illumination: bool = True
    apply_clahe: bool = True
    clahe_clip_limit: float = 3.5
    clahe_tile_grid_size: int = 8
    sharpen_amount: float = 0.35
    pdf_dpi: int = 200


class AlignmentParams(BaseModel):
    method: str = "auto"
    min_confidence: float = 0.75
    marker_search_margin: float = 0.22
    circle_min_radius: int = 8
    circle_max_radius: int = 28
    output_width: int | None = None
    output_height: int | None = None


class OMRConfig(BaseModel):
    preprocess: PreprocessParams = Field(default_factory=PreprocessParams)
    scoring: ScoringParams = Field(default_factory=ScoringParams)
    classification: ClassificationParams = Field(default_factory=ClassificationParams)
    alignment: AlignmentParams = Field(default_factory=AlignmentParams)


class BubbleEvidence(BaseModel):
    ink_ratio: float
    mean_darkness: float
    strong_dark_ratio: float
    component_area_ratio: float | None = None


class BubbleScore(BaseModel):
    option: int
    score: float
    ink_ratio: float
    mean_darkness: float
    strong_dark_ratio: float
    component_area_ratio: float | None = None
    is_faint: bool = False
    is_strong: bool = False
    state: str = "empty"

    def evidence(self) -> BubbleEvidence:
        return BubbleEvidence(
            ink_ratio=self.ink_ratio,
            mean_darkness=self.mean_darkness,
            strong_dark_ratio=self.strong_dark_ratio,
            component_area_ratio=self.component_area_ratio,
        )


class QuestionResult(BaseModel):
    status: QuestionStatus
    selected: list[int] = Field(default_factory=list)
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    scores: dict[str, float]
    bubble_evidence: dict[str, BubbleEvidence] | None = None


class AlignmentResultMeta(BaseModel):
    status: AlignmentStatus
    confidence: float
    method: str
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class AnalysisMeta(BaseModel):
    image_path: str
    template_id: str
    question_count: int
    option_count: int
    alignment: AlignmentResultMeta
    thresholds: dict[str, float]
    errors: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    meta: AnalysisMeta
    answers: dict[str, QuestionResult]
    summary: dict[str, int]


class AnswerKey(BaseModel):
    answers: dict[str, int]


class GradedQuestionResult(BaseModel):
    question_id: int
    expected: int | None
    detected_status: QuestionStatus
    detected_selected: list[int] = Field(default_factory=list)
    grading_status: GradeStatus
    is_correct: bool = False
    warnings: list[str] = Field(default_factory=list)


class GradingSummary(BaseModel):
    total_questions: int
    answered: int
    correct: int
    wrong: int
    blank: int
    multiple: int
    uncertain: int
    accuracy: float


class GradingResult(BaseModel):
    meta: dict[str, Any]
    questions: dict[str, GradedQuestionResult]
    summary: GradingSummary


@dataclass(slots=True)
class AlignedSheet:
    image: np.ndarray
    homography: np.ndarray | None
    status: AlignmentStatus
    confidence: float
    method: str
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DebugArtifacts:
    aligned_image: np.ndarray | None = None
    ink_mask: np.ndarray | None = None
    bubble_scores: list[dict[str, Any]] = field(default_factory=list)
    review_questions: dict[str, QuestionResult] = field(default_factory=dict)
    image_path: Path | None = None
