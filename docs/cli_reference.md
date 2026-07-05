# CLI Reference

## `analyze`

Analyze one image and write detection output.

```bash
python -m omr_reader analyze \
  --image samples/scans/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --out outputs/result.json \
  --debug-dir outputs/debug \
  --answer-key samples/sample_answer_key.json
```

### Important options

- `--image`: input scan or photo
- `--template`: template JSON
- `--out`: analysis output path
- `--debug-dir`: debug artifact directory
- `--config`: optional JSON or YAML config override
- `--answer-key`: optional grading input

## `build-template`

Generate a reusable template from the reference sheet.

```bash
python -m omr_reader build-template \
  --reference samples/scans/sample_sheet.png \
  --out templates/answer_sheet_template.json \
  --questions 300 \
  --columns 6 \
  --options 4
```

### Important options

- `--reference`: reference form image
- `--questions`: total number of questions
- `--columns`: number of vertical answer columns
- `--options`: number of options per question
- `--column-order`: default is `ltr`
- `--option-order`: default is `ltr`

## `batch`

Process every supported image in a directory.

```bash
python -m omr_reader batch \
  --input-dir samples/scans \
  --template templates/answer_sheet_template.json \
  --answer-key samples/sample_answer_key.json \
  --output-dir outputs/batch_results
```

### Important options

- `--input-dir`: source directory containing images
- `--template`: template JSON
- `--output-dir`: batch output root
- `--debug-dir`: optional custom folder name used inside each sample folder
- `--config`: optional JSON or YAML config override
- `--answer-key`: optional grading key for every sample
