from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .analyzer import analyze_sheet, write_analysis_result
from .template_builder import build_template_from_reference
from .template_io import load_template, save_template

app = typer.Typer(help="OMR answer sheet reader")
console = Console()


@app.command("analyze")
def analyze_command(
    image: Path = typer.Option(..., exists=True, readable=True),
    template: Path = typer.Option(..., exists=True, readable=True),
    out: Path = typer.Option(...),
    debug_dir: Path | None = typer.Option(None),
    config: Path | None = typer.Option(None, exists=True, readable=True),
) -> None:
    result = analyze_sheet(image, template, config_path=config, debug_dir=debug_dir)
    write_analysis_result(out, result)
    console.print(f"Wrote analysis to {out}")
    console.print(json.dumps(result.summary, ensure_ascii=False, indent=2))


@app.command("batch")
def batch_command(
    input_dir: Path = typer.Option(..., exists=True, file_okay=False, readable=True),
    template: Path = typer.Option(..., exists=True, readable=True),
    output_dir: Path = typer.Option(...),
    debug_dir: Path | None = typer.Option(None),
    config: Path | None = typer.Option(None, exists=True, readable=True),
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

    for image_path in images:
        per_debug = debug_dir / image_path.stem if debug_dir else None
        result = analyze_sheet(image_path, template, config_path=config, debug_dir=per_debug)
        write_analysis_result(output_dir / f"{image_path.stem}.json", result)
        table.add_row(
            image_path.name,
            str(result.summary["single"]),
            str(result.summary["blank"]),
            str(result.summary["multiple"]),
            str(result.summary["uncertain"]),
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
    column_order: str = typer.Option("rtl", help="rtl or ltr"),
    option_order: str = typer.Option("ltr", help="ltr or rtl"),
) -> None:
    template = build_template_from_reference(
        reference,
        questions,
        columns,
        options,
        template_id=template_id,
        column_order=column_order,
        option_order=option_order,
    )
    save_template(out, template)
    console.print(f"Wrote template to {out}")


def main() -> None:
    app()
