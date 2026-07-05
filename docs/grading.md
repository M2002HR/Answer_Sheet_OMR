# Grading

## Input Format

The grading workflow accepts a JSON answer key whose question set exactly matches the analyzed template.

Supported value formats:

- letters: `"a"`, `"b"`, `"c"`, `"d"`
- integers: `1`, `2`, `3`, `4`

Question IDs must match the analyzed sheet exactly.

This is especially important when:

- a printed form has physical capacity for more questions than the active exam
- a custom template is built for only the first `N` slots
- per-column question counts are used

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
