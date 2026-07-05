# Batch Processing

## Behavior

The batch command processes every supported image in the input directory.

For each sample:

- a folder named after the image stem is created
- `analysis.json` is written inside that folder
- `grading.json` is written when an answer key is provided
- debug artifacts are written to `debug/` inside the same sample folder

## Output Structure

```text
output_dir/
  batch_summary.json
  sample_sheet/
    analysis.json
    grading.json
    debug/
      aligned.png
      ink_mask.png
      bubbles_overlay.png
      bubbles_scores.csv
      questions_review.json
```

## Batch Summary

`batch_summary.json` contains:

- per-file summary information
- aggregate totals across the batch

If grading is enabled, the summary also includes grading counts such as `correct` and `wrong`.
