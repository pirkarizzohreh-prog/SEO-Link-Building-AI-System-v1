# طراحی دیتابیس — PostgreSQL

نسخه‌ی تکامل‌یافته‌ی جداول سند اولیه؛ تفاوت‌های کلیدی نسبت به سند خام کارفرما:

- افزودن `users` برای احراز هویت چندکاربره
- تفکیک `keywords` از `anchors` (در سند اولیه در دیاگرام معماری «Keyword Manager» جدا از «Anchor Manager» بود ولی در بخش دیتابیس ادغام شده بود)
- افزودن `topics` به‌عنوان خروجی مستقل Topic Generator (قبل از نگارش کامل مقاله) تا بتوان قبل از صرف توکن روی نگارش، موضوع را تأیید/رد کرد
- افزودن `ai_jobs` به‌عنوان صف‌کار + لاگ کامل فراخوانی‌های AI (شفافیت هزینه و قابلیت retry)
- افزودن `seo_audit_results` برای نگهداری جزئیات هر چک (نه فقط pass/fail کلی)
- افزودن `publications` برای جدا کردن «رکورد انتشار» از «رکورد مقاله» (یک مقاله می‌تواند بیش از یک بار تلاش انتشار داشته باشد)
- افزودن `anchor_usage_log` برای اجرای دقیق قانون توزیع انکر (۳۰/۳۵/۲۰/۱۵)

### افزوده‌های دور دوم طراحی (تأییدشده — Competitor Intelligence، Content Brief، Internal Link، Knowledge Base)

- `competitors` + `competitor_pages` + `content_gaps` → **Competitor Intelligence Module**
- `content_briefs` → **Content Brief Generator** (بین Topic و Article Writer)
- `internal_link_suggestions` → **Internal Link Suggestion Agent** (لینک‌سازی داخلی سایت هدف، مستقل از پایپ‌لاین گست‌پست)
- `project_knowledge_base` → **Project Knowledge Base** (برند/صنعت/لحن/قوانین هر پروژه، به همه‌ی ایجنت‌ها تزریق می‌شود)

## ER Overview (متنی)

```
users
projects 1───1 project_knowledge_base
projects 1───N target_pages
projects 1───N competitors ───N competitor_pages (→ optionally N target_pages)
target_pages 1───N keywords
target_pages 1───N anchors ───N anchor_usage_log
target_pages 1───N content_gaps (منبع: competitor_pages)
projects 1───N campaigns  (campaign → یک target_page مشخص)
campaigns 1───N topics
topics 1───1 content_briefs
campaigns 1───N articles ───N seo_audit_results
content_briefs 1───N articles   (هر مقاله از یک brief تولید می‌شود)
target_pages 1───N articles
anchors 1───N articles          (هر مقاله دقیقاً یک انکر/لینک خروجی دارد)
blog_platforms 1───N articles
articles 1───N publications ───N blog_platforms
projects 1───N internal_link_suggestions (source_target_page_id, destination_target_page_id → هر دو FK به target_pages)
ai_jobs (polymorphic: reference_table + reference_id → هر رکوردی)
```

## تعریف جداول (DDL توصیفی)

### `users`
| فیلد | نوع | توضیح |
|---|---|---|
| id | uuid / serial PK | |
| name | text | |
| email | text unique | |
| password_hash | text | |
| role | enum(`admin`,`editor`) | admin: مدیریت کامل، editor: فقط CRUD محتوا و تأیید |
| is_active | boolean default true | |
| created_at | timestamptz | |

### `projects`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_name | text | |
| website_url | text | |
| industry | text | |
| description | text | |
| status | enum(`active`,`inactive`) | |
| created_at / updated_at | timestamptz | |

### `project_knowledge_base`  *(جدید — Project Knowledge Base)*

رابطه ۱-به-۱ با `projects`. هدف: نگهداری متمرکز اطلاعات برند/صنعت/لحن/قوانین هر پروژه تا **همه‌ی ایجنت‌ها** (Topic Generator، Content Brief Generator، Article Writer، SEO Auditor) بدون تکرار تنظیمات، از یک منبع واحد context بگیرند.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_id | FK → projects (unique) | |
| brand_name | text | |
| brand_voice_tone | text | مثلاً «تخصصی، غیررسمی، مبتنی بر داده» |
| target_audience | text | مخاطب هدف محتوا |
| industry_context | text | توضیح تکمیلی صنعت (فراتر از فیلد کوتاه `projects.industry`) |
| style_guidelines | text | راهنمای سبک نگارش (طول جمله، اصطلاحات مجاز/غیرمجاز) |
| forbidden_words | jsonb | کلمات/ادعاهای ممنوعه (مثلاً ادعای درمانی در صنایع خاص) |
| mandatory_points | jsonb nullable | نکاتی که باید در محتوای این پروژه رعایت شود |
| sample_reference_urls | jsonb nullable | نمونه محتوای تأییدشده برای الگوبرداری لحن |
| custom_rules | jsonb nullable | قوانین آزاد اضافه (key-value) برای توسعه‌ی آینده بدون migration جدید |
| created_at / updated_at | timestamptz | |

> نکته طراحی: این جدول عمداً جدا از `projects` نگه داشته شده (نه ستون‌های اضافه روی `projects`) چون حجم متن آن نسبتاً بزرگ است و به‌ندرت نسبت به فیلدهای اصلی پروژه تغییر می‌کند؛ جداسازی، query های سبک روی لیست پروژه‌ها را تحت تأثیر قرار نمی‌دهد.

### `target_pages`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_id | FK → projects | |
| title | text | |
| url | text | |
| main_keyword | text | |
| page_type | enum(`product`,`article`,`category`) | |
| priority | int | برای اولویت‌بندی کمپین‌ها |
| created_at | timestamptz | |

### `keywords`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| target_page_id | FK → target_pages | |
| keyword | text | |
| type | enum(`main`,`related`,`semantic`) | خروجی Keyword Intelligence Agent |
| source | enum(`ai`,`manual`) | |
| created_at | timestamptz | |

### `competitors`  *(جدید — Competitor Intelligence Module)*

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_id | FK → projects | |
| name | text | |
| website_url | text | |
| notes | text nullable | |
| created_at | timestamptz | |

### `competitor_pages`  *(جدید)*

صفحات مشخصِ رقیب که برای همان `main_keyword` رتبه می‌گیرند و تحلیل می‌شوند.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| competitor_id | FK → competitors | |
| target_page_id | FK → target_pages nullable | این صفحه رقیبِ کدام صفحه‌ی ماست |
| url | text | |
| fetched_title | text nullable | |
| fetched_headings | jsonb nullable | ساختار H2/H3 استخراج‌شده |
| fetched_word_count | int nullable | |
| top_keywords | jsonb nullable | کلیدواژه‌های استخراج‌شده توسط Competitor Intelligence Agent |
| analyzed_at | timestamptz nullable | |
| created_at | timestamptz | |

### `content_gaps`  *(جدید)*

خروجی اصلی Competitor Intelligence Agent: موضوعات/کلیدواژه/هدینگ‌هایی که رقبا پوشش داده‌اند ولی محتوای ما (صفحه هدف + مقالات قبلی همان صفحه) پوشش نداده است.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| target_page_id | FK → target_pages | |
| gap_topic | text | عنوان/موضوع خلأ |
| gap_type | enum(`topic`,`keyword`,`heading`) | |
| source_competitor_page_id | FK → competitor_pages nullable | |
| status | enum(`new`,`used_in_topic`,`ignored`) | |
| created_at | timestamptz | |

> این جدول مستقیماً به‌عنوان ورودی اضافه به **Topic Generator Agent** داده می‌شود (نگاه کنید به `AI_WORKFLOW.md`) تا موضوعات پیشنهادی، خلأهای محتوایی رقبا را هم پوشش دهند.

### `anchors` (Anchor Bank)
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| target_page_id | FK → target_pages | |
| anchor_text | text | |
| anchor_type | enum(`exact`,`partial`,`semantic`,`brand`) | |
| usage_limit | int nullable | سقف دفعات استفاده (اختیاری) |
| usage_count | int default 0 | به‌روزرسانی خودکار پس از هر استفاده |
| is_active | boolean default true | |
| created_at | timestamptz | |

### `anchor_usage_log`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| anchor_id | FK → anchors | |
| article_id | FK → articles | |
| anchor_type | enum(همان مقادیر anchors.anchor_type) | denormalized برای محاسبه سریع نسبت ۳۰/۳۵/۲۰/۱۵ بدون join سنگین |
| used_at | timestamptz | |

> منطق کسب‌وکار: قبل از تولید هر مقاله، سرویس `anchor_service.pick_next_anchor(target_page_id)` با شمارش `anchor_usage_log` در ۲۰ لینک اخیرِ همان `target_page`، نوع انکر بعدی را طوری انتخاب می‌کند که نسبت Exact 30% / Partial 35% / Semantic 20% / Brand 15% حفظ شود.

### `blog_platforms`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| name | text | |
| url | text | |
| status | enum(`active`,`inactive`) | |
| username | text nullable | برای فاز ۲ (اتوماسیون) |
| password_encrypted | text nullable | باید با KMS/Fernet رمزنگاری شود، هرگز plain-text |
| login_url | text nullable | |
| category_default | text nullable | |
| last_publish_date | timestamptz nullable | |
| created_at | timestamptz | |

### `campaigns`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_id | FK → projects | |
| target_page_id | FK → target_pages | |
| name | text | |
| total_links_target | int | مثلاً ۲۰ |
| blog_count | int | تعداد وبلاگ مقصد |
| duration_days | int | مثلاً ۶۰ |
| status | enum(`planning`,`in_progress`,`completed`,`paused`) | |
| start_date / end_date | date | |
| created_at | timestamptz | |

### `topics`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| campaign_id | FK → campaigns | |
| title | text | |
| rationale | text nullable | چرا این موضوع پیشنهاد شده (خروجی AI) |
| status | enum(`suggested`,`selected`,`rejected`) | |
| generated_by | enum(`ai`,`manual`) | |
| created_at | timestamptz | |

### `content_briefs`  *(جدید — Content Brief Generator)*

بین `topics` و `articles` قرار می‌گیرد. Article Writer Agent دیگر مستقیماً از عنوان موضوع مقاله نمی‌نویسد، بلکه از یک بریف ساختاریافته استفاده می‌کند — کیفیت و یکدستی خروجی را بالا می‌برد و تعداد retry های ممیزی SEO را کاهش می‌دهد.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| topic_id | FK → topics (unique) | هر موضوعِ تأییدشده دقیقاً یک بریف دارد |
| target_page_id | FK → target_pages | |
| outline | jsonb | آرایه‌ای از `{heading, level(h2/h3), key_points[]}` |
| target_word_count | int default 1200 | |
| keywords_to_include | jsonb | ترکیبی از `keywords` صفحه هدف + `content_gaps` مرتبط |
| must_include_points | jsonb nullable | نکات الزامی (می‌تواند از `project_knowledge_base.mandatory_points` بیاید) |
| tone | text nullable | مقدار پیش‌فرض از `project_knowledge_base.brand_voice_tone` |
| source_content_gap_ids | jsonb nullable | کدام `content_gaps` در این بریف لحاظ شده (ردیابی) |
| status | enum(`draft`,`approved`) | تأیید انسانی اختیاری قبل از نگارش کامل |
| created_at | timestamptz | |

### `articles`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| campaign_id | FK → campaigns | |
| topic_id | FK → topics nullable | |
| content_brief_id | FK → content_briefs nullable | *(جدید)* بریفی که Article Writer از آن استفاده کرده؛ nullable برای سازگاری با مقالاتی که بدون بریف (fallback) تولید شده‌اند |
| target_page_id | FK → target_pages | |
| anchor_id | FK → anchors | |
| blog_platform_id | FK → blog_platforms nullable | تخصیص در زمان تولید بسته انتشار |
| title | text | |
| content | text (markdown/HTML) | |
| word_count | int | |
| seo_score | numeric nullable | خروجی SEO Auditor |
| status | enum(`draft`,`reviewed`,`approved`,`needs_human_review`,`published`,`rejected`) | |
| published_url | text nullable | |
| published_at | timestamptz nullable | |
| created_at / updated_at | timestamptz | |

### `seo_audit_results`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| article_id | FK → articles | |
| check_name | text | مثل `word_count_min`, `link_present`, `anchor_correct`, `heading_structure`, `keyword_density`, `duplicate_similarity` |
| passed | boolean | |
| score | numeric nullable | برای چک‌های عددی (مثل درصد شباهت) |
| details | text nullable | پیام توضیحی |
| created_at | timestamptz | |

### `publications`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| article_id | FK → articles | |
| blog_platform_id | FK → blog_platforms | |
| method | enum(`manual`,`automated`) | |
| status | enum(`success`,`failed`) | |
| published_url | text nullable | |
| notes | text nullable | |
| published_at | timestamptz | |

### `internal_link_suggestions`  *(جدید — Internal Link Suggestion Agent)*

**مهم:** این ماژول مستقل از پایپ‌لاین گست‌پست است. طبق قانون سند اولیه، هر مقاله‌ی لینک‌سازی (گست‌پست در وبلاگ خارجی) فقط دقیقاً **یک لینک خروجی** به سایت هدف دارد؛ بنابراین این جدول هرگز به `articles` تزریق نمی‌شود. کاربرد آن **تحلیل و پیشنهاد ساختار لینک‌دهی داخلیِ خودِ سایت پروژه** است (بین صفحات ثبت‌شده در `target_pages`) — یک خروجی/گزارش مجزا برای تیم/مشتری تا لینک‌سازی داخلی سایت را خودشان اعمال کنند.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| project_id | FK → projects | |
| source_target_page_id | FK → target_pages | صفحه‌ای که پیشنهاد می‌شود لینک از آن خارج شود |
| destination_target_page_id | FK → target_pages | صفحه‌ای که پیشنهاد می‌شود لینک به آن داده شود |
| suggested_anchor | text | |
| reason | text nullable | توضیح AI (مثلاً «هر دو صفحه حول کلیدواژه‌ی مرتبط X هستند») |
| status | enum(`suggested`,`applied`,`dismissed`) | |
| created_at | timestamptz | |

> **محدودیت دانسته‌شده در MVP**: تحلیل فقط روی صفحاتی انجام می‌شود که در `target_pages` ثبت شده‌اند، نه کل سایت (کرال کامل سایت خارج از محدوده MVP است؛ در فاز بعد قابل افزودن).

### `ai_jobs` (صف کار + لاگ AI)
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| job_type | enum(`keyword_intel`,`topic_gen`,`article_write`,`seo_audit`,`publish`,`competitor_analysis`,`brief_generation`,`internal_link_suggestion`) | *(به‌روزرسانی: ۳ نوع جدید برای ماژول‌های این مرحله)* |
| reference_table | text | مثلاً `campaigns`, `topics`, `articles` |
| reference_id | int | |
| status | enum(`pending`,`running`,`success`,`failed`) | |
| provider | enum(`openai`,`claude`) nullable | کدام LLM استفاده شد |
| input_payload | jsonb | پرامپت/پارامترها |
| output_payload | jsonb nullable | پاسخ خام |
| tokens_used | int nullable | |
| cost_estimate | numeric nullable | |
| error_message | text nullable | |
| retry_count | int default 0 | |
| created_at / started_at / finished_at | timestamptz | |

> این جدول هم نقش صف کار (worker با `WHERE status='pending' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED` آن را برمی‌دارد) و هم نقش لاگ کامل AI را دارد — برای شفافیت هزینه (که در ابزار داخلی تیم مهم است) ضروری است.

## Indexing پیشنهادی (MVP)

- `target_pages(project_id)`, `anchors(target_page_id, anchor_type)`, `articles(campaign_id, status)`, `ai_jobs(status, job_type)`, `anchor_usage_log(anchor_id, used_at)`
- Full-Text Search روی `articles.content` (`tsvector` + GIN index) برای چک شباهت ساده در MVP (قبل از رفتن به embedding vector در فاز بعد)
- `competitor_pages(competitor_id)`, `content_gaps(target_page_id, status)`
- `content_briefs(topic_id)` unique index
- `internal_link_suggestions(project_id, status)`
- `project_knowledge_base(project_id)` unique index (رابطه ۱-به-۱)
