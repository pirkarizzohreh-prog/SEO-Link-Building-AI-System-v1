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

### افزوده‌های دور سوم طراحی (تأییدشده — بهبودهای نهایی قبل از Scaffold)

- `content_templates` + `prompt_templates` → **Content Templates Module** (مدیریت انواع محتوا و نسخه‌بندی پرامپت‌ها)
- `content_status_history` → **Advanced Content Status Workflow** (لاگ کامل عبور از ۶ مرحله: Idea → Brief → Writing → Audit → Human Review → Published)
- `serp_snapshots` → **SERP Snapshot Storage** (تاریخچه تحلیل رقبا برای هر کلیدواژه)
- `link_placement_rules` → **Link Placement Rules** (قوانین کمپین به‌جای مقادیر hardcode مثل نسبت ۳۰/۳۵/۲۰/۱۵ یا «۱۰۰ کلمه اول»)
- `approvals` → **Human Approval Layer** (گیت اجباری تأیید انسانی قبل از هرگونه انتشار، حتی خودکار)

## ER Overview (متنی)

```
users
projects 1───1 project_knowledge_base
projects 1───N target_pages
projects 1───N competitors ───N competitor_pages ───1 serp_snapshots (nullable — منبع کشف)
target_pages 1───N serp_snapshots (به ازای هر keyword)
target_pages 1───N keywords
target_pages 1───N anchors ───N anchor_usage_log
target_pages 1───N content_gaps (منبع: competitor_pages)
projects 1───N campaigns  (campaign → یک target_page مشخص)
projects/campaigns 1───N link_placement_rules (scope hierarchy: global < project < campaign)
campaigns 1───N topics
topics 1───1 content_briefs ───N (content_templates — nullable، الگوی پایه)
campaigns 1───N articles ───N seo_audit_results
content_briefs 1───N articles   (هر مقاله از یک brief تولید می‌شود)
target_pages 1───N articles
anchors 1───N articles          (هر مقاله دقیقاً یک انکر/لینک خروجی دارد)
blog_platforms 1───N articles
articles 1───N publications ───N blog_platforms
articles 1───N approvals        (گیت اجباری تأیید انسانی قبل از publish)
(topics/content_briefs/articles) 1───N content_status_history (پلی‌مورفیک، لاگ ۶ مرحله‌ی Workflow)
projects 1───N internal_link_suggestions (source_target_page_id, destination_target_page_id → هر دو FK به target_pages)
ai_jobs (polymorphic: reference_table + reference_id → هر رکوردی) ───N prompt_templates (کدام نسخه پرامپت استفاده شد)
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

### `content_templates`  *(جدید — Content Templates Module)*

انواع محتوا (نه پرامپت خام) — مثلاً «مقاله آموزشی How-To»، «مقایسه‌ای»، «تحلیل روند صنعت». هر Content Brief از یک تمپلیت به‌عنوان اسکلت پایه استفاده می‌کند (قابل بازنویسی توسط AI روی همان اسکلت).

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| name | text | مثلاً «Educational How-To» |
| description | text nullable | |
| applicable_page_types | jsonb nullable | کدام `page_type` های target_page مناسب این تمپلیت‌اند (`product`/`article`/`category`) |
| default_outline_skeleton | jsonb | ساختار عمومی H2/H3 پیش‌فرض (مثلاً: مقدمه → مشکل → راه‌حل‌ها → جمع‌بندی) |
| default_word_count | int default 1200 | |
| is_active | boolean default true | |
| created_at / updated_at | timestamptz | |

### `prompt_templates`  *(جدید — Content Templates Module)*

نسخه‌بندیِ کامل پرامپت هر ایجنت — جایگزین/تکمیل‌کننده‌ی فایل‌های استاتیک `ai/prompts/*.md`؛ این جدول به تیم اجازه می‌دهد پرامپت‌ها را از طریق داشبورد ویرایش کند **بدون دیپلوی مجدد بک‌اند**، و هر تغییر یک نسخه‌ی جدید و قابل audit ثبت می‌کند (append-only، نه overwrite).

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| agent_type | enum(`keyword_intel`,`topic_gen`,`competitor_analysis`,`brief_generation`,`article_write`,`seo_audit`,`internal_link_suggestion`) | همان مقادیر `ai_jobs.job_type` (به‌جز `publish` که پرامپت LLM ندارد) |
| name | text | برچسب انسانی (مثلاً «Article Writer — v3 لحن رسمی‌تر») |
| template_text | text | متن پرامپت با placeholder (مثلاً `{{main_keyword}}`) |
| version | int | شماره نسخه، هر ویرایش نسخه جدید می‌سازد |
| is_active | boolean default true | فقط یک نسخه‌ی فعال به ازای هر `agent_type` (constraint در سطح اپلیکیشن) |
| created_by | FK → users nullable | |
| created_at | timestamptz | |

> ردیابی مصرف: هر `ai_jobs` رکورد ستون‌های `prompt_template_id` و `prompt_template_version` را ذخیره می‌کند (نگاه کنید به تعریف `ai_jobs` در پایین) تا همیشه مشخص باشد هر مقاله دقیقاً با کدام نسخه‌ی پرامپت تولید شده — برای عیب‌یابی و مقایسه کیفیت بین نسخه‌های پرامپت ضروری است.

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
| source_serp_snapshot_id | FK → serp_snapshots nullable | *(جدید)* این صفحه‌ی رقیب از کدام اسنپ‌شات SERP کشف شده |
| analyzed_at | timestamptz nullable | |
| created_at | timestamptz | |

### `serp_snapshots`  *(جدید — SERP Snapshot Storage)*

تاریخچه‌ی نتایج جست‌وجو برای یک کلیدواژه در یک لحظه‌ی مشخص — مبنای Competitor Intelligence و امکان مقایسه‌ی تغییر رتبه‌بندی در طول زمان (مثلاً «۳ ماه پیش رقیب X رتبه ۵ داشت، الان رتبه ۲»).

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| target_page_id | FK → target_pages | |
| keyword | text | کلیدواژه‌ی جست‌وجوشده (معمولاً `main_keyword`) |
| search_engine | enum(`google`) default `google` | برای توسعه‌ی آینده (Bing و…) |
| results | jsonb | آرایه‌ی `{position, url, title, snippet, domain}` |
| source | enum(`manual`,`api`) | **MVP: عمدتاً `manual`** (کاربر نتایج را وارد می‌کند یا از یک اکسپورت ساده import می‌کند)؛ اتصال زنده به SerpAPI/DataForSEO در فاز۲ |
| fetched_at | timestamptz | |
| created_at | timestamptz | |

> **تصمیم طراحی MVP**: بدون خرید/اتصال یک SERP API زنده در نسخه اول (هزینه + پیچیدگی اضافه)؛ ساختار جدول از روز اول برای هر دو مسیر (`manual` یا `api`) آماده است، بنابراین وقتی تصمیم به اتصال API زنده گرفته شد فقط یک `ai_job(type=serp_fetch)` جدید اضافه می‌شود، بدون تغییر schema.

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

### `link_placement_rules`  *(جدید — Link Placement Rules)*

تا اینجای طراحی، قوانینی مثل نسبت توزیع انکر (۳۰/۳۵/۲۰/۱۵)، «لینک در ۱۰۰ کلمه اول» و «فقط یک لینک خروجی» hardcode بودند. این جدول آن‌ها را **قابل‌تنظیم** می‌کند — چون در عمل هر پروژه/کمپین ممکن است قوانین کمی متفاوت بخواهد (مثلاً یک مشتری نسبت انکر متفاوت، یا محدودیت تعداد لینک در هر وبلاگ در ماه).

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| scope | enum(`global`,`project`,`campaign`) | سطح اعمال قانون |
| scope_id | int nullable | `project_id` یا `campaign_id`؛ برای `scope=global` مقدار null (یک ردیف پیش‌فرض سیستمی) |
| anchor_distribution | jsonb | پیش‌فرض `{"exact":30,"partial":35,"semantic":20,"brand":15}` |
| link_position_max_words | int default 100 | «لینک باید در N کلمه اول باشد» |
| max_outbound_links | int default 1 | طبق قانون سند اولیه؛ قابل تغییر برای انواع محتوای دیگر در آینده |
| max_links_per_blog_per_month | int nullable | جلوگیری از اشباع یک وبلاگ |
| min_days_between_links_same_target | int nullable | فاصله‌ی زمانی حداقلی بین دو لینک متوالی به یک صفحه هدف (drip pacing طبیعی) |
| is_active | boolean default true | |
| created_at / updated_at | timestamptz | |

> **منطق resolve (اولویت از خاص به عام)**: هنگام نیاز به یک قانون (مثلاً در `anchor_service.pick_next_anchor` یا ساخت پرامپت Article Writer)، سرویس ابتدا دنبال ردیف `scope=campaign, scope_id=<campaign.id>` می‌گردد؛ نبود → `scope=project, scope_id=<project.id>`؛ نبود → `scope=global, scope_id=null` (یک ردیف پیش‌فرض که با seed اولیه دیتابیس ساخته می‌شود). این یعنی نیازی به FK مستقیم روی `campaigns`/`projects` نیست و افزودن override برای یک کمپین خاص، migration نمی‌خواهد.

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
| content_template_id | FK → content_templates nullable | *(جدید)* اسکلت پایه‌ای که این بریف از آن شروع شده (اگر انتخاب شده باشد) |
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
| status | enum(`draft`,`in_audit`,`reviewed`,`needs_human_review`,`approved`,`published`,`rejected`) | *(به‌روزرسانی)* افزودن `in_audit` (حالت گذرا حین اجرای `ai_job(type=seo_audit)`، برای نمایش واضح در UI به‌جای ماندن در `draft`)؛ نگاشت این enum به ۶ مرحله‌ی Advanced Content Status Workflow در `AI_WORKFLOW.md` مستند شده |
| human_approved | boolean default false | *(جدید — Human Approval Layer)* فقط با ثبت رکورد در `approvals` به `true` تغییر می‌کند؛ هیچ فرآیند خودکاری مجاز به ست‌کردن مستقیم این فیلد نیست |
| human_approved_by | FK → users nullable | *(جدید)* denormalized از آخرین `approvals` رکورد، برای query سریع |
| human_approved_at | timestamptz nullable | *(جدید)* |
| published_url | text nullable | |
| published_at | timestamptz nullable | |
| created_at / updated_at | timestamptz | |

> **قانون سخت (Human Approval Layer)**: مسیر `POST /articles/{id}/publish` — چه دستی (MVP) چه خودکار با Playwright (فاز۲) — در سطح سرویس (نه فقط UI) چک می‌کند `human_approved = true` باشد؛ در غیر این صورت خطای `409 Conflict` برمی‌گرداند. هیچ ایجنت AI (نه SEO Auditor، نه هیچ job دیگر) اجازه‌ی ست‌کردن `human_approved=true` را ندارد — این فیلد فقط از طریق endpoint تأیید انسانی (`POST /articles/{id}/approve`) و با ثبت هم‌زمان یک رکورد `approvals` تغییر می‌کند.

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

### `approvals`  *(جدید — Human Approval Layer)*

لاگ **غیرقابل‌تغییر (append-only)** هر تأیید/رد انسانی در نقاط حساس پایپ‌لاین. این جدول منبع حقیقتِ گیت انتشار است؛ ستون‌های `articles.human_approved*` صرفاً denormalize سریع همین رکوردها هستند.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| entity_table | text | مثلاً `topics`, `content_briefs`, `articles` |
| entity_id | int | |
| approval_type | enum(`topic_selection`,`brief_approval`,`pre_publish`) | کدام گیتِ تأیید |
| decision | enum(`approved`,`rejected`) | |
| decided_by | FK → users | **هرگز NULL** — هیچ تأیید خودکار/سیستمی وجود ندارد |
| note | text nullable | دلیل رد یا نکته‌ی تأیید |
| created_at | timestamptz | |

> **قانون سخت**: ردیف `approval_type=pre_publish, decision=approved` پیش‌نیاز اجباریِ هر انتشار (دستی یا خودکار) است؛ endpoint انتشار (`POST /articles/{id}/publish`) و همچنین handler اتوماسیون Playwright در فاز۲ هر دو قبل از اجرا این رکورد را چک می‌کنند. این جدول هرگز توسط `ai_jobs`/ایجنت‌های AI نوشته نمی‌شود.

### `content_status_history`  *(جدید — Advanced Content Status Workflow)*

لاگ پلی‌مورفیک هر تغییر وضعیت در طول ۶ مرحله‌ی Idea → Brief → Writing → Audit → Human Review → Published (نگاشت دقیق در `AI_WORKFLOW.md`). هدف: امکان گزارش «هر مرحله چقدر طول می‌کشد» (bottleneck analysis) و یک تاریخچه‌ی قابل‌حسابرسی برای هر آیتم محتوایی، فراتر از صرفاً ستون `status` فعلیِ هر جدول.

| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| entity_table | text | `topics` / `content_briefs` / `articles` |
| entity_id | int | |
| stage | enum(`idea`,`brief`,`writing`,`audit`,`human_review`,`published`,`rejected`) | برچسب یکدست مرحله (مستقل از enum داخلی هر جدول) |
| from_status | text nullable | مقدار قبلی ستون status همان جدول |
| to_status | text | مقدار جدید |
| actor_type | enum(`ai`,`user`) | |
| actor_id | int nullable | `user_id` اگر `actor_type=user`؛ برای `ai` می‌تواند `ai_jobs.id` مرتبط باشد |
| note | text nullable | |
| created_at | timestamptz | |

> این جدول **جایگزین** `ai_jobs` نمی‌شود (آن برای لاگ فراخوانی خام LLM است)، بلکه مکمل آن است: یک نمای سطح‌بالاتر و یکدست از «این آیتم محتوایی الان در کدام مرحله از ۶ مرحله است و چه زمانی جابه‌جا شده».

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
| job_type | enum(`keyword_intel`,`topic_gen`,`article_write`,`seo_audit`,`publish`,`competitor_analysis`,`brief_generation`,`internal_link_suggestion`,`serp_fetch`) | *(به‌روزرسانی: `serp_fetch` برای اتصال آینده به SERP API؛ در MVP عملاً بلااستفاده چون منبع `manual` است)* |
| reference_table | text | مثلاً `campaigns`, `topics`, `articles` |
| reference_id | int | |
| status | enum(`pending`,`running`,`success`,`failed`) | |
| provider | enum(`openai`,`claude`) nullable | کدام LLM استفاده شد |
| prompt_template_id | FK → prompt_templates nullable | *(جدید)* کدام پرامپت استفاده شد |
| prompt_template_version | int nullable | *(جدید)* نسخه‌ی دقیق (چون `prompt_templates` می‌تواند بعداً ویرایش/نسخه‌ی جدید بگیرد) |
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
- `serp_snapshots(target_page_id, keyword, fetched_at)`
- `link_placement_rules(scope, scope_id)` — با یک partial unique index تضمین می‌کند حداکثر یک ردیف `is_active=true` به ازای هر `(scope, scope_id)`
- `prompt_templates(agent_type, is_active)` — برای واکشی سریع نسخه‌ی فعال
- `content_status_history(entity_table, entity_id, created_at)`
- `approvals(entity_table, entity_id, approval_type)`
