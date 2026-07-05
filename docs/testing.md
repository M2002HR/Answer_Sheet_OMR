# Testing

## Test Coverage Areas

The current automated tests cover:

- question classification rules
- synthetic scoring behavior
- template schema validation
- smoke analysis
- corner-marker detection on the sample sheet
- template ordering on the sample sheet
- grading logic
- YAML config loading

## Commands

Run the complete test suite:

```bash
pytest -q
```

Run a focused subset:

```bash
pytest -q tests/test_alignment_and_builder.py tests/test_grading.py
```

## What the Tests Verify

- a cyan bubble border is not counted as a filled response
- a strong dark mark produces a high score
- faint traces do not become selected answers
- multiple marks are reported correctly
- failed alignment downgrades results safely
- sample-sheet question ordering matches the required top-left to bottom-right progression
