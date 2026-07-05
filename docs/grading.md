# Grading

## Input Format

The current grading workflow accepts a JSON answer key such as `samples/sample_answer_key.json`.

Supported value formats:

- letters: `"a"`, `"b"`, `"c"`, `"d"`
- integers: `1`, `2`, `3`, `4`

Question IDs are expected to match the analyzed sheet exactly.

## Grading Rules

Per question:

- `single` and matching answer -> `correct`
- `single` and non-matching answer -> `wrong`
- `blank` -> `blank`
- `multiple` -> `multiple`
- `uncertain` -> `uncertain`

## Validation

Grading does not silently continue if the answer key does not match the analyzed question set.

It fails when:

- the answer key is missing questions
- the answer key contains extra questions
- the answer key contains invalid option values

## Output Summary

The grading summary reports:

- `total_questions`
- `answered`
- `correct`
- `wrong`
- `blank`
- `multiple`
- `uncertain`
- `accuracy`
