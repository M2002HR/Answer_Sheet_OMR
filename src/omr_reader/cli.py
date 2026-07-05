from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .analyzer import analyze_sheet, write_analysis_result
from .grading import grade_analysis_result, load_answer_key, write_grading_result
from .template_builder import build_template_from_reference
from .template_io import save_template

app = typer.Typer(help="OMR answer sheet reader")
console = Console()


@app.command("analyze")
def analyze_command(
    image: Path = typer.Option(..., exists=True, readable=True),
    template: Path = typer.Option(..., exists=True, readable=True),
    out: Path = typer.Option(...),
    debug_dir: Path | None = typer.Option(None),
    config: Path | None = typer.Option(None, exists=True, readable=True),
    answer_key: Path | None = typer.Option(None, exists=True, readable=True),
) -> None:
    result = analyze_sheet(image, template, config_path=config, debug_dir=debug_dir)
    write_analysis_result(out, result)
    console.print(f"Wrote analysis to {out}")
    console.print(json.dumps(result.summary, ensure_ascii=False, indent=2))
    if answer_key is not None:
        grading = grade_analysis_result(result, load_answer_key(answer_key), answer_key)
        grading_out = out.with_name(f"{out.stem}.grading.json")
        write_grading_result(grading_out, grading)
        console.print(f"Wrote grading to {grading_out}")
        console.print(json.dumps(grading.summary.model_dump(mode='json'), ensure_ascii=False, indent=2))


@app.command("batch")
def batch_command(
    input_dir: Path = typer.Option(..., exists=True, file_okay=False, readable=True),
    template: Path = typer.Option(..., exists=True, readable=True),
    output_dir: Path = typer.Option(...),
    debug_dir: Path | None = typer.Option(None, help="Optional debug folder name inside each sample folder."),
    config: Path | None = typer.Option(None, exists=True, readable=True),
    answer_key: Path | None = typer.Option(None, exists=True, readable=True),
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(
        path
        for path in input_dir.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    )
    table = Table(title="Batch OMR")
    table.add_column("Image")
    table.add_column("Single")
    table.add_column("Blank")
    table.add_column("Multiple")
    table.add_column("Uncertain")
    table.add_column("Correct")
    aggregate = {
        "single": 0,
        "blank": 0,
        "multiple": 0,
        "uncertain": 0,
        "needs_review": 0,
        "correct": 0,
        "wrong": 0,
        "graded_blank": 0,
        "graded_multiple": 0,
        "graded_uncertain": 0,
    }
    files: dict[str, dict[str, int | float]] = {}
    loaded_answer_key = load_answer_key(answer_key) if answer_key else None

    for image_path in images:
        sample_output_dir = output_dir / image_path.stem
        sample_output_dir.mkdir(parents=True, exist_ok=True)
        debug_folder_name = debug_dir.name if debug_dir is not None else "debug"
        per_debug = sample_output_dir / debug_folder_name
        result = analyze_sheet(image_path, template, config_path=config, debug_dir=per_debug)
        analysis_path = sample_output_dir / "analysis.json"
        write_analysis_result(analysis_path, result)
        sample_summary: dict[str, int | float] = dict(result.summary)
        for key in ["single", "blank", "multiple", "uncertain", "needs_review"]:
            aggregate[key] += result.summary[key]
        grading_correct = "-"
        if loaded_answer_key is not None:
            grading = grade_analysis_result(result, loaded_answer_key, answer_key)
            write_grading_result(sample_output_dir / "grading.json", grading)
            grading_correct = str(grading.summary.correct)
            sample_summary.update(
                {
                    "correct": grading.summary.correct,
                    "wrong": grading.summary.wrong,
                    "graded_blank": grading.summary.blank,
                    "graded_multiple": grading.summary.multiple,
                    "graded_uncertain": grading.summary.uncertain,
                    "accuracy": grading.summary.accuracy,
                }
            )
            aggregate["correct"] += grading.summary.correct
            aggregate["wrong"] += grading.summary.wrong
            aggregate["graded_blank"] += grading.summary.blank
            aggregate["graded_multiple"] += grading.summary.multiple
            aggregate["graded_uncertain"] += grading.summary.uncertain
        table.add_row(
            image_path.name,
            str(result.summary["single"]),
            str(result.summary["blank"]),
            str(result.summary["multiple"]),
            str(result.summary["uncertain"]),
            grading_correct,
        )
        files[image_path.name] = sample_summary
    (output_dir / "batch_summary.json").write_text(
        json.dumps({"files": files, "totals": aggregate}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    console.print(table)


@app.command("build-template")
def build_template_command(
    reference: Path = typer.Option(..., exists=True, readable=True),
    out: Path = typer.Option(...),
    questions: int = typer.Option(..., min=1),
    columns: int = typer.Option(..., min=1),
    options: int = typer.Option(..., min=2),
    template_id: str = typer.Option("answer_sheet_v1"),
    column_order: str = typer.Option("ltr", help="ltr or rtl"),
    option_order: str = typer.Option("ltr", help="ltr or rtl"),
    column_question_counts: str | None = typer.Option(
        None, help="Optional comma-separated question counts per column, e.g. 3,3,2"
    ),
) -> None:
    parsed_column_question_counts = None
    if column_question_counts:
        parsed_column_question_counts = [int(value.strip()) for value in column_question_counts.split(",") if value.strip()]
    template = build_template_from_reference(
        reference,
        questions,
        columns,
        options,
        template_id=template_id,
        column_order=column_order,
        option_order=option_order,
        column_question_counts=parsed_column_question_counts,
    )
    save_template(out, template)
    console.print(f"Wrote template to {out}")


def main() -> None:
    app()
