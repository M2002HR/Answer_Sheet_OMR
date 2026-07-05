# دستور کامل برای Codex: پیاده‌سازی سیستم OMR پاسخ‌برگ ثابت

می‌خواهم یک سیستم دقیق و قابل‌اعتماد برای خواندن پاسخ‌برگ تستی بسازی. ورودی سیستم یک عکس یا اسکن از پاسخ‌برگ است و خروجی باید یک JSON باشد که برای هر سؤال مشخص کند کدام گزینه علامت خورده، سؤال خالی است، چند گزینه علامت خورده، یا فقط اثر کم‌رنگ/پاک‌شده دیده شده است.

این پروژه فعلاً فقط باید تشخیص گزینه‌های علامت‌خورده را انجام دهد. تصحیح با کلید آزمون فعلاً لازم نیست.

## هدف اصلی

برای هر سؤال، سیستم باید یکی از حالت‌های زیر را تشخیص دهد:

1. `single`: دقیقاً یک گزینه معتبر علامت خورده است.
2. `blank`: هیچ گزینه معتبری علامت نخورده است.
3. `multiple`: بیشتر از یک گزینه معتبر علامت خورده است.
4. `uncertain`: سیستم مطمئن نیست و باید برای بررسی انسانی علامت بزند.

نکته بسیار مهم: اگر داوطلب اول یک گزینه را علامت زده و بعد پاک کرده، ممکن است اثر کم‌رنگی از جوهر/مداد باقی مانده باشد. چنین اثری نباید به عنوان گزینه انتخاب‌شده حساب شود. فقط باید در خروجی به شکل warning یا evidence گزارش شود.

---

## تصویر نمونه

یک نمونه از پاسخ‌برگ در پروژه قرار می‌دهم. فرض کن مسیر آن این است:

```text
assets/sample_sheet.png
```

این پاسخ‌برگ شبیه فرم‌های OMR است:

- کادرها و بیضی گزینه‌ها آبی/فیروزه‌ای هستند.
- علامت‌های دانش‌آموز سیاه یا بسیار تیره هستند.
- هر سؤال ۴ گزینه دارد.
- پاسخ‌ها در چند ستون عمودی قرار گرفته‌اند.
- احتمال وجود چرخش، اعوجاج پرسپکتیو، اسکن ناقص، نویز، سایه، فشرده‌سازی JPEG و رد پاک‌کن وجود دارد.

---

## اصل مهم طراحی

از OCR برای خواندن شماره سؤال‌ها استفاده نکن. شماره سؤال‌ها و جای گزینه‌ها در قالب ثابت هستند. این مسئله باید به شکل OMR حل شود، نه OCR.

جریان کلی باید این باشد:

```text
input image
  -> preprocessing
  -> sheet alignment / registration
  -> template-based bubble localization
  -> per-bubble mark scoring
  -> per-question classification
  -> JSON output
  -> optional debug images/reports
```

---

## زبان و تکنولوژی پیشنهادی

پروژه را با Python پیاده‌سازی کن.

نسخه پیشنهادی:

```text
Python >= 3.11
```

کتابخانه‌ها:

```text
opencv-python-headless
numpy
pydantic
typer
rich
pytest
pillow
```

در صورت نیاز برای محیط توسعه می‌توانی `opencv-python` هم استفاده کنی، ولی dependency اصلی بهتر است headless باشد.

---

## ساختار پیشنهادی پروژه

ساختار را تمیز، ماژولار و قابل تست بساز:

```text
omr-sheet-reader/
  README.md
  pyproject.toml
  requirements.txt
  assets/
    sample_sheet.png
    reference_sheet.png              # اگر تصویر مرجع تمیز داریم
  templates/
    answer_sheet_template.json
  src/
    omr_reader/
      __init__.py
      cli.py
      config.py
      models.py
      preprocess.py
      alignment.py
      template_builder.py
      template_io.py
      scoring.py
      classification.py
      analyzer.py
      debug.py
      exceptions.py
  tests/
    test_classification.py
    test_scoring_synthetic.py
    test_template_schema.py
    test_analyzer_smoke.py
  outputs/
    .gitkeep
```

---

## CLI مورد انتظار

یک CLI با `typer` بساز.

### 1. تحلیل یک عکس

```bash
python -m omr_reader analyze \
  --image assets/sample_sheet.png \
  --template templates/answer_sheet_template.json \
  --out outputs/result.json \
  --debug-dir outputs/debug
```

### 2. تحلیل دسته‌ای

```bash
python -m omr_reader batch \
  --input-dir scans/ \
  --template templates/answer_sheet_template.json \
  --output-dir outputs/batch_results \
  --debug-dir outputs/batch_debug
```

### 3. ساخت یا به‌روزرسانی قالب

```bash
python -m omr_reader build-template \
  --reference assets/reference_sheet.png \
  --out templates/answer_sheet_template.json \
  --questions 300 \
  --columns 6 \
  --options 4
```

اگر ساخت خودکار قالب سخت شد، حداقل یک ابزار نیمه‌خودکار یا config دستی بساز که بتوان مختصات ستون‌ها، فاصله سؤال‌ها و موقعیت گزینه‌ها را تعریف کرد.

---

## فرمت JSON خروجی

خروجی باید deterministic و قابل پردازش باشد.

نمونه:

```json
{
  "meta": {
    "image_path": "assets/sample_sheet.png",
    "template_id": "answer_sheet_v1",
    "question_count": 300,
    "option_count": 4,
    "alignment": {
      "status": "ok",
      "confidence": 0.97,
      "method": "homography"
    },
    "thresholds": {
      "marked_threshold": 0.22,
      "faint_threshold": 0.10,
      "uncertain_margin": 0.07
    }
  },
  "answers": {
    "1": {
      "status": "single",
      "selected": [1],
      "confidence": 0.94,
      "warnings": [],
      "scores": {
        "1": 0.81,
        "2": 0.03,
        "3": 0.04,
        "4": 0.02
      },
      "bubble_evidence": {
        "1": {"ink_ratio": 0.76, "mean_darkness": 0.84, "strong_dark_ratio": 0.69},
        "2": {"ink_ratio": 0.02, "mean_darkness": 0.04, "strong_dark_ratio": 0.00},
        "3": {"ink_ratio": 0.02, "mean_darkness": 0.05, "strong_dark_ratio": 0.00},
        "4": {"ink_ratio": 0.01, "mean_darkness": 0.03, "strong_dark_ratio": 0.00}
      }
    },
    "2": {
      "status": "blank",
      "selected": [],
      "confidence": 0.91,
      "warnings": ["faint_trace_or_erased"],
      "scores": {
        "1": 0.12,
        "2": 0.03,
        "3": 0.02,
        "4": 0.02
      }
    },
    "3": {
      "status": "multiple",
      "selected": [2, 4],
      "confidence": 0.88,
      "warnings": ["multiple_marks"],
      "scores": {
        "1": 0.04,
        "2": 0.66,
        "3": 0.03,
        "4": 0.71
      }
    }
  },
  "summary": {
    "single": 250,
    "blank": 30,
    "multiple": 10,
    "uncertain": 10,
    "needs_review": 20
  }
}
```

نکته: حتی اگر یک گزینه پاک‌شده باشد، در `selected` قرار نگیرد. فقط در `warnings` یا `bubble_evidence` گزارش شود.

---

## فرمت قالب `answer_sheet_template.json`

قالب باید مستقل از عکس ورودی باشد و روی تصویر align‌شده کار کند.

نمونه ساختار:

```json
{
  "template_id": "answer_sheet_v1",
  "version": "1.0.0",
  "reference_size": {"width": 1024, "height": 1280},
  "question_count": 300,
  "option_count": 4,
  "alignment": {
    "reference_points": [
      {"name": "top_left", "x": 52, "y": 40},
      {"name": "top_right", "x": 980, "y": 40},
      {"name": "bottom_right", "x": 980, "y": 1240},
      {"name": "bottom_left", "x": 52, "y": 1240}
    ]
  },
  "bubbles": {
    "1": [
      {"option": 1, "cx": 102, "cy": 356, "rx": 10, "ry": 6},
      {"option": 2, "cx": 129, "cy": 356, "rx": 10, "ry": 6},
      {"option": 3, "cx": 156, "cy": 356, "rx": 10, "ry": 6},
      {"option": 4, "cx": 183, "cy": 356, "rx": 10, "ry": 6}
    ]
  }
}
```

مختصات دقیق را باید از قالب واقعی یا ابزار build-template استخراج کنی. اعداد بالا فقط نمونه‌اند و نباید کورکورانه استفاده شوند.

---

## Alignment / Registration

این قسمت حیاتی است. اگر عکس حتی چند پیکسل جابه‌جا شود، تشخیص خراب می‌شود.

### الزامات alignment

1. تصویر ورودی را به اندازه و مختصات `reference_size` قالب تبدیل کن.
2. چرخش، scale، translation و perspective را اصلاح کن.
3. اگر alignment با اطمینان کافی انجام نشد، خروجی بده ولی `alignment.status = "failed"` یا `"low_confidence"` بگذار و همه سؤال‌ها را `uncertain` یا `needs_review` کن.

### روش پیشنهادی

حداقل یکی از این روش‌ها را پیاده کن و ساختار را طوری بگذار که قابل تعویض باشد:

#### روش A: پیدا کردن کادر اصلی و Homography

- تصویر را grayscale کن.
- لبه‌ها را پیدا کن.
- بزرگ‌ترین contour مستطیلی یا چهارضلعی را پیدا کن.
- چهار گوشه پاسخ‌برگ را تخمین بزن.
- با `cv2.getPerspectiveTransform` و `cv2.warpPerspective` تصویر را به اندازه مرجع تبدیل کن.

#### روش B: Feature matching با تصویر مرجع

اگر `reference_sheet.png` داریم:

- ORB یا AKAZE feature بگیر.
- match کن.
- با RANSAC homography پیدا کن.
- warpPerspective انجام بده.
- confidence را بر اساس تعداد inlierها و reprojection error محاسبه کن.

#### روش C: استفاده از نشانه‌های ثابت پاسخ‌برگ

در تصویر نمونه، بلوک‌ها/نشانگرهای سیاه کنار فرم و جدول بالای صفحه وجود دارند. اگر قابل اتکا هستند، از آن‌ها به عنوان fiducial marker کمک بگیر.

### خروجی alignment

تابع alignment باید این خروجی را بدهد:

```python
AlignedSheet(
    image=aligned_bgr,
    homography=H,
    status="ok" | "low_confidence" | "failed",
    confidence=float,
    diagnostics={...}
)
```

---

## Preprocessing

در `preprocess.py` توابع زیر را بساز:

1. `load_image(path) -> np.ndarray`
2. `normalize_image(image) -> np.ndarray`
3. `remove_shadows_or_normalize_illumination(image) -> np.ndarray`
4. `to_gray(image) -> np.ndarray`
5. `create_dark_ink_mask(image) -> np.ndarray`

### نکته مهم درباره رنگ‌ها

بیضی‌های گزینه‌ها آبی هستند، ولی علامت‌های واقعی سیاه‌اند. بنابراین scoring نباید با کادر آبی گزینه اشتباه شود.

برای تشخیص جوهر/مداد:

- از grayscale و HSV/LAB کمک بگیر.
- پیکسل‌های خیلی تیره را ink حساب کن.
- رنگ آبی/فیروزه‌ای دور گزینه را حذف کن.
- scoring را فقط در قسمت داخلی بیضی انجام بده، نه روی مرز بیضی.

---

## Bubble Scoring

تابع اصلی در `scoring.py`:

```python
def score_bubble(aligned_bgr: np.ndarray, bubble: Bubble, params: ScoringParams) -> BubbleScore:
    ...
```

مدل‌های داده‌ای پیشنهادی:

```python
class Bubble(BaseModel):
    option: int
    cx: float
    cy: float
    rx: float
    ry: float

class BubbleScore(BaseModel):
    option: int
    score: float
    ink_ratio: float
    mean_darkness: float
    strong_dark_ratio: float
    component_area_ratio: float | None = None
    is_faint: bool = False
    is_strong: bool = False
```

### روش scoring پیشنهادی

داخل بیضی را ماسک کن، ولی کوچک‌تر از خود بیضی:

```text
inner_rx = rx * 0.55 تا 0.70
inner_ry = ry * 0.55 تا 0.70
```

علت: مرز آبی گزینه نباید وارد محاسبه شود.

متریک‌ها:

1. `ink_ratio`: نسبت پیکسل‌های تیره داخل ماسک.
2. `mean_darkness`: میانگین تاریکی داخل ماسک.
3. `strong_dark_ratio`: نسبت پیکسل‌های خیلی تیره.
4. `component_area_ratio`: اندازه بزرگ‌ترین connected component تیره داخل ماسک نسبت به مساحت ماسک.

فرمول score را ساده ولی قابل تنظیم بساز:

```text
score =
  0.45 * ink_ratio +
  0.30 * mean_darkness +
  0.25 * strong_dark_ratio
```

یا اگر component قابل اتکا بود:

```text
score =
  0.35 * ink_ratio +
  0.25 * mean_darkness +
  0.25 * strong_dark_ratio +
  0.15 * component_area_ratio
```

تمام ضرایب باید در config قابل تغییر باشند.

---

## تشخیص پاک‌شده / اثر کم‌رنگ

این قسمت بسیار مهم است.

گزینه پاک‌شده معمولاً این ویژگی‌ها را دارد:

- کمی تاریکی یا خاکستری دارد.
- نسبت پیکسل‌های خیلی تیره آن کم است.
- connected component واضح و متراکم ندارد.
- score آن از blank بیشتر است ولی به اندازه mark واقعی نیست.

پس سه سطح تعریف کن:

```text
score < faint_threshold:
    empty

faint_threshold <= score < marked_threshold:
    faint_trace_or_erased

score >= marked_threshold:
    candidate_marked
```

مقادیر اولیه:

```text
faint_threshold = 0.08 تا 0.12
marked_threshold = 0.20 تا 0.28
strong_dark_min = 0.10 تا 0.18
```

ولی این‌ها باید در فایل config قابل تنظیم باشند.

شرط مهم:

یک گزینه فقط وقتی selected حساب شود که هم score کافی داشته باشد و هم شواهد قوی داشته باشد. مثلاً:

```python
is_marked = (
    score >= marked_threshold and
    strong_dark_ratio >= strong_dark_min
)
```

یا در config اجازه بده این شرط تغییر کند.

اگر score بالا بود ولی strong_dark_ratio پایین بود، آن را `uncertain` یا `faint_trace_or_erased` حساب کن، نه selected قطعی.

---

## Classification هر سؤال

تابع اصلی در `classification.py`:

```python
def classify_question(question_id: int, scores: list[BubbleScore], params: ClassificationParams) -> QuestionResult:
    ...
```

قواعد:

1. اگر alignment خراب بود:
   - همه سؤال‌ها `uncertain` شوند.

2. اگر هیچ گزینه‌ای marked نبود:
   - اگر هیچ faint هم نبود: `blank`
   - اگر یک یا چند faint بود: `blank` با warning `faint_trace_or_erased`

3. اگر دقیقاً یک گزینه marked بود:
   - `single`
   - `selected = [option]`
   - ولی اگر فاصله score گزینه اول با گزینه دوم خیلی کم بود، `uncertain` با warning `low_margin` بده.

4. اگر بیشتر از یک گزینه marked بود:
   - `multiple`
   - `selected = [options...]`
   - warning `multiple_marks`

5. اگر حالت مبهم بود:
   - `uncertain`
   - `selected` می‌تواند خالی باشد یا کاندیداها را در `candidates` بگذار.

### confidence

برای هر سؤال confidence بده:

- single: بر اساس فاصله score گزینه انتخاب‌شده از threshold و اختلاف با گزینه دوم.
- blank: بر اساس پایین بودن همه scoreها از faint_threshold.
- multiple: بر اساس واضح بودن چند گزینه.
- uncertain: confidence پایین.

---

## Dynamic Thresholding / Calibration

Threshold ثابت کافی نیست. باید امکان calibration داشته باشیم.

در هر sheet، توزیع scoreها را بررسی کن:

- بسیاری از bubbleها خالی هستند.
- bubbleهای علامت‌خورده score خیلی بالاتر دارند.
- اثرهای پاک‌شده بین این دو هستند.

یک روش ساده و قابل کنترل:

1. ابتدا با thresholdهای پیش‌فرض score بگیر.
2. distribution همه bubble scoreها را محاسبه کن.
3. اگر داده کافی بود، threshold را اندکی تطبیق بده؛ ولی هرگز خارج از بازه امن نرو.

مثلاً:

```text
marked_threshold بین 0.18 و 0.32
faint_threshold بین 0.06 و 0.14
```

در نسخه اول، dynamic threshold را optional کن:

```json
"adaptive_thresholds": true
```

اگر adaptive باعث رفتار غیرقابل پیش‌بینی شد، بتوانیم خاموشش کنیم.

---

## Debug خروجی‌ها

حتماً debug بساز. چون این پروژه حساس است و بدون debug نمی‌شود thresholdها را تنظیم کرد.

اگر `--debug-dir` داده شد، فایل‌های زیر را ذخیره کن:

```text
outputs/debug/
  aligned.png
  ink_mask.png
  bubbles_overlay.png
  bubbles_scores.csv
  questions_review.json
```

### bubbles_overlay.png

روی تصویر align‌شده برای هر bubble دایره/بیضی بکش:

- selected: دور پررنگ یا سبز
- blank: خاکستری
- faint/erased: زرد یا نارنجی
- multiple: قرمز
- uncertain: بنفش

اگر نمی‌خواهی رنگ‌ها را در تست‌ها سخت کنی، فقط در debug استفاده کن.

### bubbles_scores.csv

ستون‌ها:

```text
question_id,option,cx,cy,score,ink_ratio,mean_darkness,strong_dark_ratio,component_area_ratio,state
```

این فایل برای تنظیم threshold خیلی مهم است.

---

## Error Handling

خطاها را واضح مدیریت کن.

موارد خطا:

1. تصویر خوانده نشد.
2. template نامعتبر است.
3. تعداد گزینه‌ها برای یک سؤال ناقص است.
4. alignment شکست خورد.
5. تصویر خیلی تاریک/روشن/کوچک است.
6. فایل خروجی قابل نوشتن نیست.

در همه حالت‌ها CLI باید پیام قابل فهم بدهد و در صورت امکان JSON خروجی شامل `meta.errors` تولید کند.

---

## مدل‌های داده‌ای پیشنهادی با Pydantic

در `models.py` بساز:

```python
from pydantic import BaseModel, Field
from typing import Literal

QuestionStatus = Literal["single", "blank", "multiple", "uncertain"]
AlignmentStatus = Literal["ok", "low_confidence", "failed"]

class Bubble(BaseModel):
    option: int
    cx: float
    cy: float
    rx: float
    ry: float

class Template(BaseModel):
    template_id: str
    version: str = "1.0.0"
    reference_size: dict
    question_count: int
    option_count: int
    bubbles: dict[str, list[Bubble]]

class BubbleEvidence(BaseModel):
    ink_ratio: float
    mean_darkness: float
    strong_dark_ratio: float
    component_area_ratio: float | None = None

class QuestionResult(BaseModel):
    status: QuestionStatus
    selected: list[int] = Field(default_factory=list)
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    scores: dict[str, float]
    bubble_evidence: dict[str, BubbleEvidence] | None = None

class AlignmentResultMeta(BaseModel):
    status: AlignmentStatus
    confidence: float
    method: str

class AnalysisResult(BaseModel):
    meta: dict
    answers: dict[str, QuestionResult]
    summary: dict
```

ساختار دقیق را می‌توانی بهتر کنی، ولی JSON خروجی باید با نیاز بالا سازگار باشد.

---

## تست‌ها

حتماً تست بنویس. این پروژه بدون تست قابل اعتماد نیست.

### Unit test برای classification

سناریوها:

1. یک گزینه واضح:

```text
[0.80, 0.02, 0.03, 0.04] -> single option 1
```

2. خالی:

```text
[0.02, 0.03, 0.01, 0.04] -> blank
```

3. اثر پاک‌شده:

```text
[0.12, 0.03, 0.02, 0.04] -> blank + faint_trace_or_erased
```

4. چند گزینه:

```text
[0.70, 0.03, 0.68, 0.02] -> multiple [1, 3]
```

5. مرزی:

```text
[0.23, 0.19, 0.03, 0.02] -> uncertain یا single با warning low_margin
```

### تست scoring synthetic

با OpenCV تصویر مصنوعی بساز:

- bubble خالی با مرز آبی
- bubble پر با لکه سیاه
- bubble با اثر کم‌رنگ خاکستری
- bubble با نویز نقطه‌ای

باید مطمئن شوی:

- مرز آبی به عنوان mark حساب نمی‌شود.
- لکه سیاه واضح score بالا می‌گیرد.
- اثر کم‌رنگ score متوسط می‌گیرد ولی selected نمی‌شود.
- نویز کوچک selected نمی‌شود.

### Smoke test

روی `assets/sample_sheet.png` اجرا کن و فقط بررسی کن:

- برنامه crash نکند.
- JSON معتبر تولید شود.
- تعداد سؤال‌ها با template برابر باشد.
- برای هر سؤال دقیقاً ۴ score وجود داشته باشد.

---

## کیفیت و دقت مورد انتظار

به جای اینکه فقط کدی بنویسی که روی یک عکس جواب دهد، معماری باید برای عکس‌های واقعی مقاوم باشد.

مواردی که باید در نظر بگیری:

1. عکس کمی چرخیده باشد.
2. عکس پرسپکتیو داشته باشد.
3. اسکن روشن یا تاریک باشد.
4. JPEG artifacts وجود داشته باشد.
5. بخشی از برگه کمی سایه داشته باشد.
6. دانش‌آموز علامت را کامل پر نکرده باشد.
7. علامت از بیضی بیرون زده باشد.
8. رد پاک‌کن باقی مانده باشد.
9. دو گزینه علامت خورده باشد.
10. گزینه‌ای خیلی کم‌رنگ علامت خورده باشد.
11. برگه ناقص crop شده باشد.

در حالت‌های خراب، سیستم نباید با اعتماد کاذب خروجی قطعی بدهد. باید `uncertain` یا `needs_review` تولید کند.

---

## نکات پیاده‌سازی مهم

### 1. داخل بیضی را بخوان، نه کل ROI را

اگر کل ROI را بخوانی، مرز آبی گزینه وارد score می‌شود و خطا ایجاد می‌کند.

### 2. score خام را همیشه خروجی بده

حتی اگر classification درست باشد، برای تنظیم threshold به score خام نیاز داریم.

### 3. debug را از اول جدی بگیر

بدون `aligned.png` و `bubbles_overlay.png` نمی‌شود فهمید مشکل از alignment است یا scoring.

### 4. template را validate کن

اگر یک سؤال ۴ bubble نداشت، برنامه باید خطای واضح بدهد.

### 5. همه پارامترها config باشند

Thresholdها، ضرایب score، اندازه inner mask، حداقل confidence alignment و غیره نباید hard-code شوند.

### 6. خروجی reproducible باشد

با یک input و template ثابت، خروجی باید همیشه یکسان باشد.

---

## فایل config پیشنهادی

یک config پیش‌فرض در کد داشته باش و امکان override از فایل JSON/YAML هم بده.

نمونه:

```json
{
  "scoring": {
    "inner_rx_scale": 0.62,
    "inner_ry_scale": 0.62,
    "dark_pixel_threshold": 120,
    "strong_dark_threshold": 80,
    "weights": {
      "ink_ratio": 0.45,
      "mean_darkness": 0.30,
      "strong_dark_ratio": 0.25,
      "component_area_ratio": 0.00
    }
  },
  "classification": {
    "faint_threshold": 0.10,
    "marked_threshold": 0.22,
    "strong_dark_min": 0.08,
    "uncertain_margin": 0.07,
    "adaptive_thresholds": false,
    "min_marked_threshold": 0.18,
    "max_marked_threshold": 0.32
  },
  "alignment": {
    "method": "auto",
    "min_confidence": 0.75,
    "output_width": 1024,
    "output_height": 1280
  }
}
```

---

## الگوریتم پیشنهادی مرحله به مرحله

### analyze(image_path, template_path, config)

1. تصویر را بخوان.
2. config و template را بخوان و validate کن.
3. تصویر را normalize کن.
4. تصویر را با template align کن.
5. اگر alignment شکست خورد:
   - خروجی JSON با `alignment.status = failed` بده.
   - همه سؤال‌ها را `uncertain` کن.
   - debug تصویر ورودی را ذخیره کن.
6. برای هر سؤال:
   - ۴ bubble را از template بگیر.
   - برای هر bubble score بگیر.
   - سؤال را classify کن.
7. summary بساز.
8. JSON را ذخیره کن.
9. اگر debug فعال بود، overlay و csv بساز.
10. خروجی را به stdout هم چاپ کن یا مسیر فایل را اعلام کن.

---

## تعریف دقیق `needs_review`

در summary، سؤال‌های زیر باید needs_review حساب شوند:

- `status = uncertain`
- `status = multiple`
- `warnings` شامل `faint_trace_or_erased`
- `warnings` شامل `low_margin`
- alignment کم‌اعتماد

---

## معیار پذیرش نهایی

پیاده‌سازی وقتی قابل قبول است که:

1. CLIهای `analyze` و `batch` کار کنند.
2. JSON خروجی مطابق schema باشد.
3. همه سؤال‌ها در خروجی وجود داشته باشند.
4. هر سؤال برای هر ۴ گزینه score داشته باشد.
5. اثر پاک‌شده با score متوسط selected نشود.
6. debug image و CSV تولید شود.
7. تست‌های unit و synthetic پاس شوند.
8. کد ماژولار باشد و thresholdها hard-code نشده باشند.
9. اگر alignment شکست خورد، خروجی قطعی اشتباه ندهد و وضعیت را low confidence/failed اعلام کند.
10. README شامل نحوه نصب، اجرا، ساخت template، تنظیم threshold و توضیح خروجی باشد.

---

## اولویت‌بندی پیاده‌سازی

به ترتیب زیر جلو برو:

### فاز ۱: هسته OMR بدون alignment پیچیده

- template JSON بخوان.
- فرض کن تصویر already aligned است.
- scoring و classification را کامل کن.
- JSON و debug تولید کن.
- تست classification و scoring synthetic را بنویس.

### فاز ۲: alignment

- document contour یا feature matching را اضافه کن.
- aligned.png ذخیره کن.
- confidence alignment بده.

### فاز ۳: template builder

- یا auto-detection از bubbleهای آبی.
- یا ابزار نیمه‌خودکار برای تولید مختصات از ستون‌ها.

### فاز ۴: adaptive threshold و batch processing

- تحلیل دسته‌ای.
- CSVها و summary کلی.
- تنظیم threshold با داده‌های واقعی.

---

## خواسته نهایی از Codex

لطفاً این پروژه را کامل پیاده‌سازی کن، نه فقط یک اسکریپت کوتاه. کد باید production-minded، قابل تست، قابل تنظیم و قابل debug باشد.

قبل از شروع، فایل‌ها و ساختار پروژه را بساز. سپس فاز ۱ را کامل کن و تست‌ها را اجرا کن. بعد فاز ۲ و بقیه را اضافه کن. در هر مرحله کد را طوری بنویس که اگر template یا عکس واقعی تغییر کرد، فقط config/template عوض شود، نه منطق اصلی.
