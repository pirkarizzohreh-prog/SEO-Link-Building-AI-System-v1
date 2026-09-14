# Workflow تولید مقاله با AI

## نگاشت ایجنت‌ها به معماری فنی (به‌روزرسانی‌شده)

| Agent | پیاده‌سازی فنی | نوع اجرا |
|---|---|---|
| Project Knowledge Base | جدول `project_knowledge_base` — نه یک "ایجنت" بلکه یک منبع context ثابت که به پرامپت همه‌ی ایجنت‌های زیر تزریق می‌شود | بدون فراخوانی مستقل؛ فقط data injection |
| Competitor Intelligence Agent *(جدید)* | تحلیل صفحات رقیب + استخراج Content Gap | فراخوانی LLM (+ یک fetch ساده HTTP برای محتوای صفحه رقیب) |
| SEO Strategist (سند اولیه) | ترکیب `Keyword Intelligence Agent` + `Topic Generator Agent` | فراخوانی LLM |
| Content Brief Generator *(جدید)* | تبدیل Topic تأییدشده + Keywords + Content Gaps + Knowledge Base → یک بریف ساختاریافته (outline) | فراخوانی LLM (خروجی JSON ساختاریافته) |
| Content Writer (سند اولیه) | `Article Writer Agent` — اکنون از روی Content Brief می‌نویسد، نه فقط عنوان موضوع | فراخوانی LLM |
| SEO Reviewer (سند اولیه) | `SEO Auditor Agent` = چک‌های **دترمینیستیک** (کد) + یک چک کیفی سبک با LLM | ترکیبی |
| Internal Link Suggestion Agent *(جدید)* | تحلیل مستقل صفحات `target_pages` یک پروژه برای پیشنهاد لینک‌دهی داخلی سایت | فراخوانی LLM؛ **مستقل از پایپ‌لاین گست‌پست** |
| Publisher (سند اولیه) | `Publication Manager` (MVP: دستی / فاز۲: Playwright) | بدون LLM |
| Report Manager (سند اولیه) | Aggregation با SQL | بدون LLM |

## دیاگرام State Machine مقاله (به‌روزرسانی‌شده)

```
                         ┌───────────────────────────────┐
                         │  project_knowledge_base موجود  │  ← تنظیم یک‌بار در سطح پروژه،
                         │  (برند/صنعت/لحن/قوانین)        │    به همه‌ی ایجنت‌های زیر تزریق می‌شود
                         └───────────────┬─────────────────┘
                                         │ (context ثابت)
 [رقبا ثبت شدند - اختیاری، مستقل از زمان‌بندی کمپین]
        │
        ▼
 competitor_analysis (ai_job) ──▶ competitor_pages[] + content_gaps[] ذخیره می‌شود
        │
        ▼
 [campaign.start]
        │
        ▼
 keyword_intel (ai_job) ──▶ keywords[] ذخیره می‌شود
        │
        ▼
 topic_gen (ai_job، ورودی اضافه: content_gaps مرتبط) ──▶ topics[status=suggested]
        │
        ▼
   (تأیید انسانی - Dashboard)
        │
        ▼
 topics[status=selected]
        │
        ▼
 brief_generation (ai_job) ──▶ content_briefs[status=draft]   ◀── NEW STEP
        │
        ▼
   (تأیید انسانی اختیاری روی بریف)
        │
        ▼
 content_briefs[status=approved]
        │
        ▼
 article_write (ai_job، ورودی اصلی = content_brief، نه فقط topic.title) ──▶ articles[status=draft]
        │
        ▼
 seo_audit (ai_job) ──┬─▶ PASS ──▶ articles[status=reviewed]
        │              │
        │              └─▶ FAIL ──▶ retry (max 2 بار، فیدبک audit به پرامپت تزریق می‌شود)
        │                              │
        │                              └─▶ بعد از ۲ شکست ──▶ articles[status=needs_human_review]
        ▼
   (تأیید انسانی - Dashboard)
        │
        ▼
 articles[status=approved]
        │
        ▼
 publish (manual در MVP / ai_job در فاز۲) ──▶ articles[status=published] + publications[record]


 ── مسیر مستقل و موازی (بدون اتصال به مراحل بالا) ──
 [کاربر: "Analyze Internal Links" روی یک پروژه]
        │
        ▼
 internal_link_suggestion (ai_job) ──▶ internal_link_suggestions[] (گزارش/دشبورد جدا)
```

## مرحله به مرحله

### مرحله ۰ — Project Knowledge Base (پیش‌نیاز، یک‌بار در سطح پروژه)
قبل از اجرای هر پایپ‌لاینی، کاربر (یا پیش‌فرض خالی) اطلاعات `project_knowledge_base` را تنظیم می‌کند: نام برند، لحن، مخاطب هدف، صنعت، قوانین ممنوعه/الزامی. این بلوک به‌صورت یک **system context ثابت** به ابتدای پرامپت هر یک از ایجنت‌های زیر اضافه می‌شود (Competitor Intelligence برای تشخیص ارتباط gap با صنعت، Topic Generator، Content Brief Generator، Article Writer برای لحن، و حتی SEO Auditor برای چک «طبیعی بودن لحن» نسبت‌به برند). اگر خالی باشد، پرامپت‌ها بدون این بلوک اجرا می‌شوند (backward-compatible).

### مرحله ۱ — Competitor Intelligence Agent *(جدید — قبل یا موازی با شروع کمپین)*
- **ورودی**: URL صفحه(های) رقیب که کاربر برای یک `target_page` ثبت کرده (`competitors` + `competitor_pages`).
- **پردازش**: fetch محتوای صفحه رقیب (HTTP ساده در MVP؛ بدون رندر جاوااسکریپت سنگین) → استخراج heading structure و کلیدواژه‌های پرتکرار → مقایسه با `keywords` و مقالات قبلیِ همان `target_page`.
- **خروجی**: ردیف‌های `content_gaps` با `gap_type` مشخص (`topic`/`keyword`/`heading`).
- **پرامپت (خلاصه)**:
  > «متن و ساختار هدینگ صفحه‌ی رقیب زیر را با کلیدواژه‌ها و موضوعات فعلی ما مقایسه کن. موضوعات یا زیرعنوان‌هایی که رقیب پوشش داده و ما نداده‌ایم را به‌صورت JSON لیست کن.»
- **مصرف‌کننده‌ی خروجی**: مرحله ۳ (Topic Generator) و مرحله ۴ (Content Brief Generator) — نه اتصال مستقیم به نگارش مقاله.
- این مرحله **اختیاری و مستقل از زمان‌بندی کمپین** است؛ کاربر می‌تواند هر زمان رقیب اضافه/آنالیز کند و gapها در استخر جمع می‌شوند تا زمانی که کمپین بعدی از آن‌ها استفاده کند.

### مرحله ۲ — Keyword Intelligence Agent
- **ورودی**: `target_page` (title, url, main_keyword).
- **خروجی**: `keywords` (type=`related`/`semantic`).
- **پرامپت (خلاصه)**: بدون تغییر نسبت به نسخه قبلی طراحی.

### مرحله ۳ — Topic Generator Agent *(ورودی تقویت‌شده)*
- **ورودی**: `main_keyword` + `related topics` + **`content_gaps` وضعیت `new` مرتبط با همان target_page** + `project_knowledge_base`.
- **قانون سخت‌گیرانه (سند اولیه، بدون تغییر)**: موضوعات نباید تبلیغاتی باشند.
- **خروجی**: N موضوع در `topics` (`status=suggested`)؛ هر موضوعی که از یک content_gap مشخص الهام گرفته باشد، آن gap به `used_in_topic` تغییر وضعیت می‌دهد (ردیابی).
- **پرامپت (خلاصه، به‌روزرسانی‌شده)**:
  > «بر اساس کلیدواژه‌های زیر و همچنین خلأهای محتوایی که در تحلیل رقبا شناسایی شده (لیست content_gaps)، {N} عنوان مقاله‌ی آموزشی/تخصصی (غیرتبلیغاتی) پیشنهاد بده. در صورت وجود لحن برند در Knowledge Base، عناوین با آن لحن هماهنگ باشند.»
- **تأیید انسانی**: بدون تغییر.

### مرحله ۴ — Content Brief Generator *(جدید — بین Topic و Article Writer)*
- **هدف**: قبل از نگارش کامل مقاله (که پرهزینه‌ترین فراخوانی LLM در کل پایپ‌لاین است)، یک بریف ساختاریافته و قابل‌بازبینی تولید شود — کاهش retry ممیزی SEO و افزایش یکدستی کیفیت بین نویسندگان مختلف (LLM ها).
- **ورودی**: `topic` تأییدشده + `keywords` صفحه هدف + `content_gaps` مرتبط (`status=used_in_topic`) + `project_knowledge_base` (لحن/قوانین).
- **خروجی**: رکورد `content_briefs` شامل:
  - `outline`: آرایه `{heading, level, key_points[]}` (اسکلت H2/H3 پیشنهادی)
  - `target_word_count` (پیش‌فرض ۱۲۰۰، قابل افزایش برای موضوعات پیچیده‌تر)
  - `keywords_to_include`
  - `must_include_points` (از Knowledge Base یا content gap ها)
  - `tone` (از Knowledge Base)
- **پرامپت (خلاصه)**:
  > «برای موضوع «{topic.title}» یک بریف محتوایی ساختاریافته (خروجی JSON طبق اسکیمای مشخص) بساز: اسکلت H2/H3، نکات کلیدی هر بخش، کلیدواژه‌های لازم، و نکات الزامی برند. مقاله نهایی توسط نویسنده‌ای دیگر از روی این بریف نوشته خواهد شد، پس دقیق و قابل‌اجرا بنویس.»
- **تأیید انسانی (اختیاری در MVP)**: کاربر می‌تواند بریف را ویرایش/تأیید کند قبل از رفتن به نگارش؛ برای سرعت بیشتر می‌توان این تأیید را در تنظیمات کمپین "auto-approve" کرد.

### مرحله ۵ — Article Writer Agent *(ورودی اصلی اکنون Content Brief است)*
- **پیش‌نیاز انکر**: انتخاب انکر مناسب توسط `anchor_service.pick_next_anchor(target_page_id)` طبق نسبت ۳۰/۳۵/۲۰/۱۵.
- **پرامپت اصلی (طبق سند اولیه، بدون تغییر در قوانین سخت‌گیرانه، + بخش‌های جدید)**:

  ```
  تو یک متخصص SEO و نویسنده تخصصی هستی.
  یک مقاله برای وبلاگ خارجی بنویس.

  [در صورت وجود project_knowledge_base: بلوک لحن/برند/قوانین اینجا تزریق می‌شود]

  از بریف محتوایی زیر پیروی کن (اسکلت H2/H3 و نکات کلیدی هر بخش):
  {content_brief.outline}

  کلیدواژه‌های لازم برای گنجاندن طبیعی: {content_brief.keywords_to_include}
  نکات الزامی: {content_brief.must_include_points}

  لینک هدف: {target_page.url}
  انکر متن (باید دقیقاً همین باشد): {anchor.anchor_text}

  قوانین:
  - حداقل {content_brief.target_word_count} کلمه (پیش‌فرض 1200)
  - لحن انسانی
  - ساختار H2/H3 دقیقاً طبق بریف
  - بدون تبلیغات مستقیم
  - لینک در 100 کلمه اول
  - فقط یک لینک خروجی (دقیقاً همان URL و انکر داده‌شده، نه بیشتر)
  - انکر طبیعی
  - عدم keyword stuffing
  - مناسب انتشار در وبلاگ تخصصی

  خروجی را به‌صورت Markdown با H2/H3 مشخص بازگردان.
  ```
- **خروجی**: رکورد `articles` (با `content_brief_id` تنظیم‌شده) با `status=draft`.
- در صورت retry بعد از شکست audit، فیدبک auditor به همین پرامپت اضافه می‌شود (بدون تغییر بریف، مگر خطا از جنس ساختار باشد).

### مرحله ۶ — SEO Auditor Agent (ترکیبی: کد + LLM)
بدون تغییر نسبت به نسخه قبلی طراحی؛ فقط یک چک اختیاری اضافه می‌شود:

| چک | روش |
|---|---|
| تعداد کلمات ≥ حد بریف | شمارش کلمات |
| وجود لینک | regex |
| صحت URL/Anchor | تطبیق دقیق |
| موقعیت لینک در ۱۰۰ کلمه اول | offset متن |
| فقط یک لینک خروجی | شمارش |
| وجود H2/H3 مطابق outline بریف | *(جدید)* مقایسه هدینگ‌های تولیدشده با `content_brief.outline` — هشدار (نه رد سخت) اگر انحراف زیاد باشد |
| Keyword Density معقول | نسبت تکرار |
| عدم شباهت به مقالات قبلی | trigram similarity (MVP) |
| لحن هماهنگ با Knowledge Base | چک کیفی LLM با در نظر گرفتن `forbidden_words` |

منطق pass/fail و retry بدون تغییر (حداکثر ۲ retry خودکار، سپس `needs_human_review`).

### مرحله ۷ — Publication Manager
بدون تغییر نسبت به نسخه قبلی (نسخه اول MVP دستی، نسخه دوم فاز۲ خودکار با Playwright).

### مرحله ۸ — Internal Link Suggestion Agent *(جدید — مسیر مستقل، خارج از پایپ‌لاین بالا)*
- **چرا مستقل؟** قانون سخت سند اولیه این است که هر مقاله‌ی لینک‌سازی (گست‌پست) فقط **یک** لینک خروجی دارد؛ بنابراین این ایجنت هرگز در جریان نگارش مقاله اجرا نمی‌شود. کاربرد آن تحلیل **ساختار داخلی سایتِ خودِ پروژه** است، جدا از فرآیند گست‌پست.
- **ورودی**: تمام `target_pages` یک پروژه (title, main_keyword, url).
- **پردازش**: LLM صفحات را دوبه‌دو از نظر ارتباط موضوعی می‌سنجد و پیشنهاد می‌دهد کدام صفحه باید به کدام صفحه‌ی دیگر (با چه انکری) لینک بدهد تا ساختار لینک‌دهی داخلی سایت تقویت شود.
- **پرامپت (خلاصه)**:
  > «فهرست صفحات زیر (عنوان + کلیدواژه اصلی + URL) متعلق به یک سایت است. جفت‌صفحاتی که از نظر موضوعی مرتبط‌اند و باید به هم لینک داخلی بدهند را همراه با متن انکر پیشنهادی مشخص کن.»
- **خروجی**: `internal_link_suggestions` (`status=suggested`)، قابل مشاهده در یک تب مجزا از دشبورد (نه در جریان تأیید مقاله).
- **محدودیت MVP**: فقط صفحات ثبت‌شده در `target_pages` تحلیل می‌شوند (نه کرال کامل سایت).

### مرحله ۹ — Report Manager (بدون AI)
بدون تغییر؛ می‌توان در فاز بعد یک بخش گزارش «وضعیت Content Gaps پوشش‌داده‌شده» و «وضعیت پیشنهادهای لینک داخلی اعمال‌شده» هم اضافه کرد (خارج از MVP فعلی).

## اصول طراحی پرامپت (به‌روزرسانی‌شده)

- هر پرامپت در فایل جدا (`ai/prompts/*.md`) نگهداری می‌شود؛ شامل پرامپت‌های جدید: `competitor_analysis.md`, `brief_generation.md`, `internal_link_suggestion.md`.
- بلوک `project_knowledge_base` به‌صورت یک partial/snippet مشترک (`prompts/_kb_context.md`) در ابتدای پرامپت‌های Topic Generator، Content Brief Generator، Article Writer و SEO Auditor include می‌شود — یک‌بار نوشته، همه‌جا استفاده می‌شود.
- خروجی همه‌ی ایجنت‌های ساختاریافته (keywords، topics، content_gaps، content_briefs، internal_link_suggestions) باید **JSON اسکیمای مشخص** بگیرند (`response_format=json_schema` در OpenAI یا tool-use در Claude).
- هر فراخوانی LLM از طریق Interface یکسان (`LLMProvider.generate(prompt, schema=None)`) رد می‌شود؛ لاگ token/cost یکنواخت در `ai_jobs` برای همه‌ی ۸ نوع job (دو نوع قبلی اضافه‌شده: `competitor_analysis`, `brief_generation`, `internal_link_suggestion`).
- Retry با فیدبک: بدون تغییر نسبت به نسخه قبلی.
- **ترتیب هزینه‌ای پایپ‌لاین**: Competitor Intelligence و Keyword Intelligence و Topic Generator و Brief Generation همگی نسبت به Article Writer فراخوانی‌های **ارزان‌تر** هستند (پرامپت کوتاه‌تر، خروجی کوچک‌تر). قرار گرفتن Brief Generator قبل از Article Writer دقیقاً برای این طراحی شده که خطاهای ساختاری زودتر (با هزینه کمتر) گرفته شوند تا صرفاً بعد از نگارش کامل ۱۲۰۰+ کلمه‌ای.
