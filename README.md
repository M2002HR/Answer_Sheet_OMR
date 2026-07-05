# OMR Sheet Reader

A production-minded, template-based Optical Mark Recognition (OMR) pipeline for fixed multiple-choice answer sheets.

The project focuses on:

- robust sheet alignment using fixed corner markers
- deterministic template-based bubble localization
- mark scoring that avoids counting the cyan/blue bubble outline as a response
- detection-aware classification for `single`, `blank`, `multiple`, and `uncertain`
- optional grading against an answer key
- debug artifacts for calibration and human review
- batch processing with one output folder per input sample

## Features

- `analyze`: read one sheet and produce `analysis.json`
- `build-template`: generate a reusable template from a reference form
- `batch`: process a whole folder of scans
- optional grading with `answer_key.json`
- debug outputs:
  - `aligned.png`
  - `ink_mask.png`
  - `bubbles_overlay.png`
  - `bubbles_scores.csv`
  - `questions_review.json`

## Python Version

The project is tested in this workspace with Python `3.10.19` and is designed to run on Python `3.10+`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Build a Template

For the sample form included in the repository:

```bash
python -m omr_reader build-template \
  --reference assets/sample_sheet.png \
  --out templates/answer_sheet_template.json \
  --questions 300 \
  --columns 6 \
  --options 4
```

The current template is ordered exactly as follows:

- Question `1` starts at the top-left answer column.
- Numbering continues downward to the bottom of the column.
- The next question after the bottom of a column starts at the top of the next column to the right.
- Question `300` is the bottom-right question.

## Analyze One Sheet

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --out outputs/result.json \
  --debug-dir outputs/debug
```

With grading:

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --answer-key assets/answer_key.json \
  --out outputs/result.json \
  --debug-dir outputs/debug
```

This writes:

- `outputs/result.json`
- `outputs/result.grading.json` when `--answer-key` is provided
- debug artifacts inside `outputs/debug/`

## Batch Processing

```bash
python -m omr_reader batch \
  --input-dir scans/ \
  --template templates/answer_sheet_template.json \
  --answer-key assets/answer_key.json \
  --output-dir outputs/batch_results \
  --debug-dir outputs/batch_debug
```

For each input image, the batch command creates one output folder named after the sample file stem:

```text
outputs/batch_results/
  sample_001/
    analysis.json
    grading.json
    debug/
      aligned.png
      ink_mask.png
      bubbles_overlay.png
      bubbles_scores.csv
      questions_review.json
```

The batch root also contains `batch_summary.json`.

## Configuration

Default configuration is loaded from code. You can override values with JSON or YAML.

Example:

```json
{
  "scoring": {
    "inner_rx_scale": 0.62,
    "inner_ry_scale": 0.62,
    "dark_pixel_threshold": 120,
    "strong_dark_threshold": 80
  },
  "classification": {
    "faint_threshold": 0.10,
    "marked_threshold": 0.22,
    "strong_dark_min": 0.08,
    "uncertain_margin": 0.07,
    "adaptive_thresholds": false
  },
  "alignment": {
    "min_confidence": 0.75
  }
}
```

Use it like this:

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --config config.yaml \
  --out outputs/result.json
```

## Output Files

### Analysis JSON

- `meta`: image path, template ID, alignment status, thresholds, and errors
- `answers`: per-question detection result
- `summary`: counts for `single`, `blank`, `multiple`, `uncertain`, and `needs_review`

### Grading JSON

- `meta`: image, template, and answer-key reference
- `questions`: per-question grading result
- `summary`: counts for `correct`, `wrong`, `blank`, `multiple`, `uncertain`, `answered`, and overall `accuracy`

## Documentation

Detailed documentation is available in [docs/](docs):

- [docs/architecture.md](docs/architecture.md)
- [docs/cli_reference.md](docs/cli_reference.md)
- [docs/template_and_ordering.md](docs/template_and_ordering.md)
- [docs/grading.md](docs/grading.md)
- [docs/batch_processing.md](docs/batch_processing.md)
- [docs/debug_outputs.md](docs/debug_outputs.md)
- [docs/json_outputs.md](docs/json_outputs.md)
- [docs/testing.md](docs/testing.md)

## Current Sample-Sheet Result

On `assets/sample_sheet.png`, the current detection result is:

- `single = 294`
- `blank = 6`
- `multiple = 0`
- `uncertain = 0`
- `needs_review = 0`
