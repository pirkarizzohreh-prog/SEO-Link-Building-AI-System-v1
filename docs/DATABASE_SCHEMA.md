# طراحی دیتابیس — PostgreSQL

نسخه‌ی تکامل‌یافته‌ی جداول سند اولیه؛ تفاوت‌های کلیدی نسبت به سند خام کارفرما:

- افزودن `users` برای احراز هویت چندکاربره
- تفکیک `keywords` از `anchors` (در سند اولیه در دیاگرام معماری «Keyword Manager» جدا از «Anchor Manager» بود ولی در بخش دیتابیس ادغام شده بود)
- افزودن `topics` به‌عنوان خروجی مستقل Topic Generator (قبل از نگارش کامل مقاله) تا بتوان قبل از صرف توکن روی نگارش، موضوع را تأیید/رد کرد
- افزودن `ai_jobs` به‌عنوان صف‌کار + لاگ کامل فراخوانی‌های AI (شفافیت هزینه و قابلیت retry)
- افزودن `seo_audit_results` برای نگهداری جزئیات هر چک (نه فقط pass/fail کلی)
- افزودن `publications` برای جدا کردن «رکورد انتشار» از «رکورد مقاله» (یک مقاله می‌تواند بیش از یک بار تلاش انتشار داشته باشد)
- افزودن `anchor_usage_log` برای اجرای دقیق قانون توزیع انکر (۳۰/۳۵/۲۰/۱۵)

## ER Overview (متنی)

```
users
projects 1───N target_pages
target_pages 1───N keywords
target_pages 1───N anchors ───N anchor_usage_log
projects 1───N campaigns  (campaign → یک target_page مشخص)
campaigns 1───N topics
campaigns 1───N articles ───N seo_audit_results
target_pages 1───N articles
anchors 1───N articles          (هر مقاله دقیقاً یک انکر/لینک خروجی دارد)
blog_platforms 1───N articles
articles 1───N publications ───N blog_platforms
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

### `articles`
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| campaign_id | FK → campaigns | |
| topic_id | FK → topics nullable | |
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

### `ai_jobs` (صف کار + لاگ AI)
| فیلد | نوع | توضیح |
|---|---|---|
| id | serial PK | |
| job_type | enum(`keyword_intel`,`topic_gen`,`article_write`,`seo_audit`,`publish`) | |
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
