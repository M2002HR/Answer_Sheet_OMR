# Architecture

## Overview

The pipeline is organized as:

```text
input image
  -> preprocessing
  -> alignment
  -> template-based bubble localization
  -> per-bubble scoring
  -> per-question classification
  -> optional grading
  -> JSON output
  -> optional debug artifacts
```

## Main Modules

- `preprocess.py`: image loading, normalization, grayscale conversion, dark-ink masking
  - includes grayscale contrast enhancement and PDF rasterization support
- `alignment.py`: corner marker detection and perspective alignment
- `template_builder.py`: semi-automatic template generation from the reference form
- `template_io.py`: template persistence and validation
- `scoring.py`: bubble mask generation and evidence scoring
- `classification.py`: question-level decision logic
- `analyzer.py`: end-to-end sheet analysis orchestration
- `grading.py`: answer-key loading and grading
- `debug.py`: overlay, CSV, and review-artifact generation
- `cli.py`: user-facing command-line interface

## Design Goals

- deterministic output
- explicit validation
- high observability through debug artifacts
- safe handling of low-confidence alignment or ambiguous marks
- modular structure for later extension
