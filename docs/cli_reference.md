# CLI Reference

## `analyze`

Analyze one image and write detection output.

```bash
python -m omr_reader analyze \
  --image samples/scans/202512061032_Page_01.png \
  --template templates/answer_sheet_template.json \
  --out outputs/result.json \
  --debug-dir outputs/debug
```

### Important options

- `--image`: input scan or photo
- `--template`: template JSON
- `--out`: analysis output path
- `--debug-dir`: debug artifact directory
- `--config`: optional JSON or YAML config override
- `--answer-key`: optional grading input
- `--marked-threshold`: override the minimum score required for a marked bubble
- `--faint-threshold`: override the faint-trace lower band
- `--allow-multiple-marks`: preserve true multi-mark detections
- `--single-mark-only`: collapse multi-mark candidates to the highest-scoring option
- `--dark-pixel-threshold`: override the dark-pixel cutoff
- `--strong-dark-threshold`: override the strong-dark cutoff
- `--clahe-clip-limit`: override local contrast enhancement strength
- `--clahe-tile-grid-size`: override CLAHE tile size
- `--sharpen-amount`: override post-enhancement sharpening
- `--pdf-dpi`: override PDF rasterization DPI

## `build-template`

Generate a reusable template from the reference sheet.

```bash
python -m omr_reader build-template \
  --reference samples/scans/202512061032_Page_01.png \
  --out templates/answer_sheet_template.json \
  --questions 8 \
  --columns 3 \
  --options 4 \
  --column-question-counts 3,3,2
```

### Important options

- `--reference`: reference form image
- `--questions`: total number of questions
- `--columns`: number of vertical answer columns
- `--options`: number of options per question
- `--column-order`: default is `ltr`
- `--option-order`: default is `ltr`
- `--column-question-counts`: optional comma-separated explicit counts per column, such as `3,3,2`

## `batch`

Process every supported image in a directory.

```bash
python -m omr_reader batch \
  --input-dir samples/scans \
  --template templates/answer_sheet_template.json \
  --output-dir outputs/batch_results
```

### Important options

- `--input-dir`: source directory containing images
- `--template`: template JSON
- `--output-dir`: batch output root
- `--debug-dir`: optional custom folder name used inside each sample folder
- `--config`: optional JSON or YAML config override
- `--answer-key`: optional grading key for every sample
- `--marked-threshold`: batch-wide threshold override
- `--allow-multiple-marks`: preserve true multi-mark detections
- `--single-mark-only`: collapse multi-mark candidates to the highest-scoring option
- `--pdf-dpi`: PDF rasterization DPI for PDF inputs
