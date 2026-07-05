# OMR Sheet Reader

سیستم ماژولار OMR برای خواندن پاسخ‌برگ ثابت با تمرکز روی:

- `alignment` قابل اعتماد با نشانگرهای گوشه
- `template-based bubble localization`
- `scoring` مقاوم در برابر رد پاک‌کن و علامت کم‌رنگ
- خروجی JSON deterministic
- debug artifacts برای تنظیم threshold و بررسی انسانی

## نصب

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

این پروژه در این workspace با Python `3.10.19` تست شده و با Python `3.10+` اجرا می‌شود.

## ساخت Template

برای فرم نمونه موجود در پروژه:

```bash
python -m omr_reader build-template \
  --reference assets/sample_sheet.png \
  --out templates/answer_sheet_template.json \
  --questions 300 \
  --columns 6 \
  --options 4
```

builder به‌صورت نیمه‌خودکار از رنگ آبی bubbleها، ناحیه اصلی پاسخ‌ها و markerهای گوشه استفاده می‌کند. برای فرم نمونه، خروجی `templates/answer_sheet_template.json` آماده تولید شده است.

## تحلیل یک تصویر

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --out outputs/result.json \
  --debug-dir outputs/debug
```

## تحلیل دسته‌ای

```bash
python -m omr_reader batch \
  --input-dir scans/ \
  --template templates/answer_sheet_template.json \
  --output-dir outputs/batch_results \
  --debug-dir outputs/batch_debug
```

## تنظیم Threshold و Config

بدون config اضافی، تنظیمات پیش‌فرض از کد خوانده می‌شوند. برای override می‌توان فایل `JSON` داد:

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

نمونه استفاده:

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --config config.json \
  --out outputs/result.json
```

## خروجی‌ها

فایل `result.json` شامل سه بخش اصلی است:

- `meta`: مسیر تصویر، شناسه template، وضعیت alignment و thresholdهای مؤثر
- `answers`: نتیجه هر سؤال شامل `status`, `selected`, `warnings`, `scores`, `bubble_evidence`
- `summary`: شمارش `single`, `blank`, `multiple`, `uncertain`, `needs_review`

اگر `--debug-dir` داده شود این artifactها هم ساخته می‌شوند:

- `aligned.png`
- `ink_mask.png`
- `bubbles_overlay.png`
- `bubbles_scores.csv`
- `questions_review.json`

## وضعیت فعلی فرم نمونه

روی `assets/sample_sheet.png` خروجی فعلی سیستم:

- `single = 294`
- `blank = 6`
- `multiple = 0`
- `uncertain = 0`
- `needs_review = 0`
