# JSON Outputs

## Analysis JSON

Top-level shape:

```json
{
  "meta": {},
  "answers": {},
  "summary": {}
}
```

### `meta`

- `image_path`
- `template_id`
- `question_count`
- `option_count`
- `alignment`
- `thresholds`
- `errors`

### `answers`

Each question contains:

- `status`
- `selected`
- `confidence`
- `warnings`
- `scores`
- `bubble_evidence`

### `summary`

- `single`
- `blank`
- `multiple`
- `uncertain`
- `needs_review`

## Grading JSON

Top-level shape:

```json
{
  "meta": {},
  "questions": {},
  "summary": {}
}
```

### `questions`

Each question contains:

- `question_id`
- `expected`
- `detected_status`
- `detected_selected`
- `grading_status`
- `is_correct`
- `warnings`

### `summary`

- `total_questions`
- `answered`
- `correct`
- `wrong`
- `blank`
- `multiple`
- `uncertain`
- `accuracy`

## Batch Summary JSON

`batch_summary.json` contains:

- `files`: one summary object per input image
- `totals`: aggregate counters across the whole batch
