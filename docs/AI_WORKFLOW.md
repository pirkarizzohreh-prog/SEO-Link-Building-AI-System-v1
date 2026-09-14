# Workflow تولید مقاله با AI

## نگاشت ایجنت‌های سند اولیه به معماری فنی

| Agent در PRD | پیاده‌سازی فنی | نوع اجرا |
|---|---|---|
| SEO Strategist | ترکیب `Keyword Intelligence Agent` + `Topic Generator Agent` | فراخوانی LLM |
| Content Writer | `Article Writer Agent` | فراخوانی LLM |
| SEO Reviewer | `SEO Auditor Agent` = چک‌های **دترمینیستیک** (کد، بدون هزینه LLM) + یک چک کیفی با LLM | ترکیبی |
| Publisher | `Publication Manager` (MVP: دستی / فاز۲: Playwright) | بدون LLM |
| Report Manager | Aggregation با SQL | **بدون LLM** (تصمیم طراحی: چون گزارش صرفاً جمع‌بندی داده‌ی موجود در DB است، فراخوانی مدل زبانی هزینه/تأخیر بی‌مورد اضافه می‌کند) |

## دیاگرام State Machine مقاله

```
 [campaign.start]
        │
        ▼
 keyword_intel (ai_job) ──▶ keywords[] ذخیره می‌شود
        │
        ▼
 topic_gen (ai_job) ──▶ topics[status=suggested] (چند گزینه)
        │
        ▼
   (تأیید انسانی - Dashboard)
        │
        ▼
 topics[status=selected]
        │
        ▼
 article_write (ai_job) ──▶ articles[status=draft]
        │
        ▼
 seo_audit (ai_job) ──┬─▶ PASS ──▶ articles[status=reviewed]
        │              │
        │              └─▶ FAIL ──▶ retry (max 2 بار، با تزریق فیدبک audit در پرامپت)
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
```

## مرحله به مرحله

### مرحله ۱ — تعریف کمپین (بدون AI)
ورودی کاربر: پروژه، صفحه هدف، تعداد لینک هدف، تعداد وبلاگ، مدت زمان. رکورد `campaigns` ساخته می‌شود با `status=planning`.

### مرحله ۲ — Keyword Intelligence Agent
- **ورودی**: `target_page` (title, url, main_keyword) — در صورت نیاز می‌توان محتوای صفحه را هم fetch کرد (فاز بعد؛ در MVP فقط از فیلدهای موجود در DB استفاده می‌شود تا وابستگی به scraping نداشته باشیم).
- **خروجی**: لیست `Related Topics` که در جدول `keywords` (type=`related`/`semantic`) ذخیره می‌شود.
- **پرامپت (خلاصه)**:
  > «تو یک متخصص تحقیق کلمات کلیدی SEO هستی. صفحه هدف با کلیدواژه اصلی «{main_keyword}» را تحلیل کن و ۵ تا ۸ موضوع/کلیدواژه مرتبط (related topics) برای تولید محتوای لینک‌سازی پیشنهاد بده. خروجی را فقط به‌صورت JSON لیست بازگردان.»

### مرحله ۳ — Topic Generator Agent
- **ورودی**: `main_keyword` + `related topics` + تعداد مقالات موردنیاز کمپین.
- **قانون سخت‌گیرانه (از سند اولیه)**: موضوعات نباید تبلیغاتی باشند.
- **خروجی**: N موضوع در جدول `topics` با `status=suggested`.
- **پرامپت (خلاصه)**:
  > «بر اساس کلیدواژه‌های زیر، {N} عنوان مقاله‌ی آموزشی/تخصصی (غیرتبلیغاتی) برای انتشار در وبلاگ‌های شخص ثالث پیشنهاد بده. عناوین نباید نام برند یا محصول را مستقیم تبلیغ کنند، باید برای خواننده‌ی عمومی آن صنعت ارزش آموزشی داشته باشند.»
- **تأیید انسانی**: کاربر در Dashboard موضوعات را می‌بیند و `approve`/`reject` می‌کند (جلوگیری از هدررفت توکن روی موضوعات نامناسب).

### مرحله ۴ — Article Writer Agent
- **پیش‌نیاز**: انتخاب انکر مناسب توسط `anchor_service.pick_next_anchor(target_page_id)` طبق نسبت ۳۰/۳۵/۲۰/۱۵ (با query روی `anchor_usage_log`).
- **پرامپت اصلی (طبق سند اولیه، بدون تغییر در قوانین)**:

  ```
  تو یک متخصص SEO و نویسنده تخصصی هستی.
  یک مقاله برای وبلاگ خارجی بنویس.

  موضوع: {topic.title}
  کلیدواژه اصلی: {main_keyword}
  لینک هدف: {target_page.url}
  انکر متن (باید دقیقاً همین باشد): {anchor.anchor_text}

  قوانین:
  - حداقل 1200 کلمه
  - لحن انسانی
  - ساختار H2/H3
  - بدون تبلیغات مستقیم
  - لینک در 100 کلمه اول
  - فقط یک لینک خروجی (دقیقاً همان URL و انکر داده‌شده، نه بیشتر)
  - انکر طبیعی (در جمله‌ای طبیعی جا بگیرد، نه چسبیده و مصنوعی)
  - عدم keyword stuffing
  - مناسب انتشار در وبلاگ تخصصی

  خروجی را به‌صورت Markdown با H2/H3 مشخص بازگردان.
  ```
- **خروجی**: رکورد `articles` با `status=draft`، `word_count` محاسبه‌شده، و ثبت لاگ کامل در `ai_jobs`.
- در صورت retry (بعد از شکست audit)، خروجی گزارش auditor به‌عنوان بخش «اصلاحات لازم» به همین پرامپت اضافه می‌شود.

### مرحله ۵ — SEO Auditor Agent (ترکیبی: کد + LLM)

چک‌های **دترمینیستیک** (بدون فراخوانی LLM، ارزان و سریع — در `seo_audit_service.py`):

| چک | روش |
|---|---|
| تعداد کلمات ≥ ۱۲۰۰ | شمارش کلمات متن |
| وجود لینک | regex برای markdown link / `<a href>` |
| صحت URL | تطبیق دقیق با `target_page.url` |
| صحت Anchor | تطبیق متن انکر با `anchor.anchor_text` |
| موقعیت لینک در ۱۰۰ کلمه اول | بررسی offset لینک در متن |
| فقط یک لینک خروجی | شمارش تعداد لینک‌های خروجی (باید=۱) |
| وجود H2/H3 | شمارش هدینگ‌های markdown |
| Keyword Density معقول | نسبت تکرار `main_keyword` به کل کلمات (رد اگر > حد آستانه، مثلاً ۳٪) |
| عدم شباهت به مقالات قبلی | **MVP**: مقایسه با PostgreSQL Full-Text Search / trigram similarity (`pg_trgm`) بین این مقاله و مقالات قبلیِ همان `target_page`؛ رد اگر شباهت > حد آستانه (مثلاً ۸۵٪). **فاز۲**: ارتقا به embedding similarity. |

چک **کیفی با LLM** (فقط یک فراخوانی سبک):
> «متن زیر را از نظر طبیعی بودن لحن (غیر رباتیک بودن) و عدم شباهت به تبلیغ مستقیم ارزیابی کن و امتیاز ۰ تا ۱۰۰ بده + دلیل.»

هر چک به‌صورت یک ردیف در `seo_audit_results` ذخیره می‌شود؛ `articles.seo_score` میانگین وزنی است. اگر همه‌ی چک‌های سخت (hard checks: تعداد کلمه، لینک، انکر، URL) پاس نشوند → مقاله رد و به مرحله ۴ برای بازنویسی برمی‌گردد (حداکثر ۲ بار retry خودکار)، در غیر این صورت `status=needs_human_review`.

### مرحله ۶ — Publication Manager

**نسخه اول (MVP - Manual):**
1. سیستم یک `blog_platform` مناسب را به‌صورت round-robin/کمترین‌استفاده اخیر از بین وبلاگ‌های `active` پیشنهاد می‌دهد.
2. Endpoint `GET /articles/{id}/publish-package` خروجی آماده می‌دهد: `{blog, title, content, anchor, url, category}`.
3. کاربر دستی در وبلاگ منتشر می‌کند و از طریق `POST /articles/{id}/publish` نتیجه (URL نهایی) را ثبت می‌کند → `publications` رکورد جدید + `articles.status=published`.

**نسخه دوم (Phase 2 - Automated):**
- `ai_job(type=publish)` ایجاد می‌شود → یک Playwright script مخصوص همان `blog_platform` (در `automation/publishers/`) اجرا می‌شود: Login → Create Post → Insert Content → Insert Link → Publish → بازگرداندن URL نهایی.
- خطاهای اتوماسیون (مثل تغییر ساختار صفحه لاگین) در `ai_jobs.error_message` ثبت و برای بررسی انسانی flag می‌شود؛ هرگز silent fail.

### مرحله ۷ — Report Manager (بدون AI)
Query های تجمیعی روی DB (نه LLM):
- تعداد لینک‌های ساخته‌شده به تفکیک `project`/`campaign`
- صفحات هدف تقویت‌شده (چند لینک هرکدام گرفته‌اند)
- Anchor Distribution واقعی در برابر هدف ۳۰/۳۵/۲۰/۱۵ (هشدار اگر انحراف زیاد شود)
- لیست کامل URLهای منتشرشده با تاریخ

## اصول طراحی پرامپت (برای پیاده‌سازی)

- هر پرامپت در فایل جدا (`ai/prompts/*.md`) نگهداری می‌شود، نه hardcode در کد — تغییر پرامپت بدون تغییر کد.
- خروجی agentهای ساختاریافته (topics، keywords) باید **JSON اسکیمای مشخص** بگیرند (با `response_format=json_schema` در OpenAI یا tool-use در Claude) تا parse مطمئن باشد، نه parse متن آزاد.
- هر فراخوانی LLM از طریق Interface یکسان (`LLMProvider.generate(prompt, schema=None)`) رد می‌شود تا لاگ token/cost یکنواخت در `ai_jobs` ثبت شود، صرف‌نظر از provider.
- Retry با فیدبک: وقتی auditor رد می‌کند، دلایل رد به‌صورت متن ساختاریافته («این ایرادها را اصلاح کن: ...») به پرامپت نگارش بعدی اضافه می‌شود، نه فقط "دوباره بنویس".
