# Batch Processing

## Behavior

The batch command processes every supported image in the input directory.

Supported input types:

- PNG
- JPEG
- BMP
- TIFF
- PDF

For each sample:

- a folder named after the image stem is created
- `analysis.json` is written inside that folder
- `grading.json` is written when an answer key is provided
- debug artifacts are written to `debug/` inside the same sample folder
- for PDF inputs, the first page is rasterized before analysis

## Output Structure

```text
output_dir/
  batch_summary.json
  202512061032_Page_01/
    analysis.json
    debug/
      aligned.png
      ink_mask.png
      bubbles_overlay.png
      bubbles_scores.csv
      questions_review.json
```

If grading is enabled, `grading.json` is also written inside each sample folder.

## Batch Summary

`batch_summary.json` contains:

- per-file summary information
- aggregate totals across the batch

If grading is enabled, the summary also includes grading counts such as `correct` and `wrong`.
