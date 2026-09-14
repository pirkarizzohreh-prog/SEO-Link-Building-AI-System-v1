# API Specification — v1

Base URL: `/api/v1`
Auth: `Authorization: Bearer <JWT>` (به‌جز `/auth/login`)
فرمت خطا: `{ "detail": "..." }` مطابق پیش‌فرض FastAPI

## Auth

| Method | Path | توضیح |
|---|---|---|
| POST | `/auth/login` | ورود با email/password → `{access_token, refresh_token}` |
| POST | `/auth/refresh` | تمدید access token |
| GET | `/auth/me` | اطلاعات کاربر لاگین‌شده |

## Projects

| Method | Path | توضیح |
|---|---|---|
| GET | `/projects` | لیست پروژه‌ها (pagination + filter status) |
| POST | `/projects` | ایجاد پروژه |
| GET | `/projects/{id}` | جزئیات پروژه |
| PUT | `/projects/{id}` | ویرایش |
| DELETE | `/projects/{id}` | حذف (soft delete پیشنهادی) |
| GET | `/projects/{id}/target-pages` | صفحات هدف آن پروژه |

## Project Knowledge Base *(جدید)*

رابطه ۱-به-۱ با پروژه؛ اطلاعات برند/صنعت/لحن/قوانین که به همه‌ی ایجنت‌های AI تزریق می‌شود.

| Method | Path | توضیح |
|---|---|---|
| GET | `/projects/{id}/knowledge-base` | دریافت (اگر هنوز ساخته نشده، ۴۰۴ یا آبجکت خالی پیش‌فرض) |
| PUT | `/projects/{id}/knowledge-base` | ایجاد یا به‌روزرسانی کامل (upsert) — `{brand_name, brand_voice_tone, target_audience, industry_context, style_guidelines, forbidden_words[], mandatory_points[], sample_reference_urls[], custom_rules{}}` |

## Content Templates & Prompt Templates *(جدید — Content Templates Module)*

مدیریت انواع محتوا (اسکلت پایه‌ی بریف) و نسخه‌بندی پرامپت هر ایجنت — بدون نیاز به دیپلوی مجدد برای تغییر پرامپت.

| Method | Path | توضیح |
|---|---|---|
| GET | `/content-templates` | لیست تمپلیت‌های محتوا (فیلتر `applicable_page_types`) |
| POST | `/content-templates` | ایجاد تمپلیت جدید `{name, description, applicable_page_types[], default_outline_skeleton, default_word_count}` |
| PUT | `/content-templates/{id}` | ویرایش |
| DELETE | `/content-templates/{id}` | حذف (فقط اگر بریفی به آن وابسته نباشد) |
| GET | `/prompt-templates?agent_type=article_write` | لیست نسخه‌های پرامپت یک ایجنت (تاریخچه کامل) |
| GET | `/prompt-templates/{agent_type}/active` | دریافت نسخه‌ی فعال فعلی |
| POST | `/prompt-templates` | ثبت نسخه‌ی جدید `{agent_type, name, template_text}` → خودکار `version+1` و `is_active=true` (نسخه قبلی `is_active=false` می‌شود) |

## Target Pages

| Method | Path | توضیح |
|---|---|---|
| POST | `/projects/{project_id}/target-pages` | ایجاد صفحه هدف |
| GET | `/target-pages/{id}` | جزئیات + keywords + anchors مرتبط |
| PUT | `/target-pages/{id}` | ویرایش |
| DELETE | `/target-pages/{id}` | حذف |
| GET | `/target-pages/{id}/keywords` | لیست کلیدواژه‌ها |
| POST | `/target-pages/{id}/keywords` | افزودن دستی کلیدواژه |

## Competitor Intelligence *(جدید)*

| Method | Path | توضیح |
|---|---|---|
| GET | `/projects/{id}/competitors` | لیست رقبای ثبت‌شده برای پروژه |
| POST | `/projects/{id}/competitors` | افزودن رقیب `{name, website_url, notes}` |
| DELETE | `/competitors/{id}` | حذف |
| POST | `/competitors/{id}/pages` | ثبت یک صفحه‌ی رقیب برای تحلیل `{url, target_page_id}` |
| POST | `/competitor-pages/{id}/analyze` | اجرای `ai_job(type=competitor_analysis)` روی این صفحه → استخراج headings/keywords + مقایسه با `target_page` مرتبط و ثبت `content_gaps` |
| GET | `/target-pages/{id}/content-gaps` | لیست خلأهای محتوایی شناسایی‌شده (فیلتر `status`) |
| POST | `/content-gaps/{id}/ignore` | نادیده‌گرفتن یک gap (مثلاً نامرتبط تشخیص داده شد) |

## SERP Snapshots *(جدید — SERP Snapshot Storage)*

تاریخچه‌ی نتایج جست‌وجو برای کلیدواژه‌های هر صفحه هدف — پایه‌ی Competitor Intelligence و مبنای مقایسه‌ی تغییر رتبه در طول زمان.

| Method | Path | توضیح |
|---|---|---|
| GET | `/target-pages/{id}/serp-snapshots?keyword=...` | تاریخچه‌ی اسنپ‌شات‌های یک کلیدواژه (مرتب بر اساس `fetched_at`) |
| POST | `/target-pages/{id}/serp-snapshots` | ثبت دستی یک اسنپ‌شات `{keyword, results: [{position, url, title, snippet, domain}], source: "manual"}` — **MVP**: بدون اتصال زنده به SERP API |
| POST | `/competitor-pages/{id}/link-serp-snapshot` | اتصال یک `competitor_page` موجود به اسنپ‌شاتی که از آن کشف شده (`source_serp_snapshot_id`) |

## Anchor Bank

| Method | Path | توضیح |
|---|---|---|
| GET | `/target-pages/{id}/anchors` | لیست انکرها |
| POST | `/target-pages/{id}/anchors` | افزودن انکر |
| PUT | `/anchors/{id}` | ویرایش (مثلاً غیرفعال کردن) |
| DELETE | `/anchors/{id}` | حذف |
| GET | `/target-pages/{id}/anchors/distribution` | نسبت فعلی استفاده Exact/Partial/Semantic/Brand در برابر هدفِ resolve‌شده از `link_placement_rules` (پیش‌فرض ۳۰/۳۵/۲۰/۱۵، قابل override در سطح پروژه/کمپین) |

## Blog Platforms

| Method | Path | توضیح |
|---|---|---|
| GET | `/blog-platforms` | لیست |
| POST | `/blog-platforms` | افزودن وبلاگ جدید |
| PUT | `/blog-platforms/{id}` | ویرایش (وضعیت، دسته‌بندی پیش‌فرض) |
| DELETE | `/blog-platforms/{id}` | حذف |

## Link Placement Rules *(جدید — Link Placement Rules)*

قوانین کمپین (نسبت انکر، محدودیت موقعیت لینک، سقف انتشار در هر وبلاگ...) به‌صورت قابل‌تنظیم در سه سطح `global`/`project`/`campaign`.

| Method | Path | توضیح |
|---|---|---|
| GET | `/link-placement-rules/resolve?campaign_id=...` | قانون نهایی resolve‌شده برای یک کمپین (campaign → project → global) |
| GET | `/link-placement-rules?scope=project&scope_id=1` | لیست قوانین ثبت‌شده در یک سطح |
| POST | `/link-placement-rules` | ایجاد قانون جدید `{scope, scope_id, anchor_distribution, link_position_max_words, max_outbound_links, max_links_per_blog_per_month, min_days_between_links_same_target}` |
| PUT | `/link-placement-rules/{id}` | ویرایش |
| DELETE | `/link-placement-rules/{id}` | حذف (برمی‌گردد به سطح عمومی‌تر) |

## Campaigns

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns` | لیست (filter بر اساس project_id, status) |
| POST | `/campaigns` | ایجاد کمپین `{project_id, target_page_id, total_links_target, blog_count, duration_days}` |
| GET | `/campaigns/{id}` | جزئیات + پیشرفت (چند مقاله published از چند مورد هدف) + قانون فعال (`link_placement_rules` resolve‌شده) |
| PUT | `/campaigns/{id}` | ویرایش |
| POST | `/campaigns/{id}/start` | **شروع Pipeline** → ایجاد `ai_job(type=keyword_intel)` و سپس زنجیره‌ی خودکار تا `topic_gen`؛ از این نقطه به بعد، `anchor_service` و `article_write` قوانین را از `link_placement_rules` (نه مقدار hardcode) resolve می‌کنند |
| POST | `/campaigns/{id}/pause` | توقف موقت |

## Topics *(Stage: Idea)*

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns/{id}/topics` | لیست موضوعات پیشنهادی |
| POST | `/topics/{id}/approve` | *(به‌روزرسانی)* تأیید موضوع → آماده برای تولید بریف؛ یک رکورد `approvals(approval_type=topic_selection, decision=approved)` + یک رکورد `content_status_history(stage=idea→brief)` ثبت می‌کند |
| POST | `/topics/{id}/reject` | رد موضوع (`approvals(decision=rejected)`) |
| POST | `/topics/{id}/generate-brief` | *(جدید، جایگزین فراخوانی مستقیم generate-article)* ایجاد `ai_job(type=brief_generation)` → خروجی یک رکورد `content_briefs` |

## Content Briefs *(جدید — Content Brief Generator، Stage: Brief)*

بین Topic و Article Writer؛ خروجی این مرحله ورودی اصلی نگارش مقاله می‌شود.

| Method | Path | توضیح |
|---|---|---|
| GET | `/topics/{id}/brief` | دریافت بریف تولیدشده برای این موضوع |
| PUT | `/content-briefs/{id}` | ویرایش دستی بریف قبل از نگارش (outline، کلیدواژه‌ها، نکات الزامی) |
| POST | `/content-briefs/{id}/approve` | تأیید بریف → `status=approved`؛ ثبت `approvals(approval_type=brief_approval)` + `content_status_history(stage=brief→writing)` |
| POST | `/content-briefs/{id}/generate-article` | *(جایگزین مسیر قبلی)* ایجاد `ai_job(type=article_write)` با استفاده از این بریف و تمپلیت مرتبط (`content_template_id`، اختیاری) |

## Articles *(Stage: Writing → Audit → Human Review → Published)*

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns/{id}/articles` | لیست مقالات کمپین با فیلتر status |
| GET | `/articles/{id}` | جزئیات کامل مقاله + بریف مرتبط + نتایج SEO Audit + تاریخچه `content_status_history` |
| PUT | `/articles/{id}` | ویرایش دستی محتوا/عنوان (قبل از انتشار) |
| POST | `/articles/{id}/audit` | اجرای مجدد `ai_job(type=seo_audit)` → `status=in_audit` سپس `reviewed`/`needs_human_review` |
| POST | `/articles/{id}/approve` | *(به‌روزرسانی — Human Approval Layer)* تنها راه تغییر `human_approved=true`؛ ثبت اجباری `approvals(approval_type=pre_publish, decision=approved, decided_by=<user>)` + `content_status_history(stage=human_review→published)`؛ بدون این فراخوانی، `human_approved` همیشه `false` می‌ماند |
| POST | `/articles/{id}/reject` | تغییر status → `rejected` (+ دلیل)؛ `approvals(decision=rejected)` |
| POST | `/articles/{id}/publish` | **قبل از اجرا چک می‌کند `human_approved=true`، در غیر این صورت `409 Conflict`.** MVP (manual): ثبت `published_url` دستی؛ فاز۲ (automated): trigger کردن `ai_job(type=publish)` — همان چک روی handler اتوماسیون هم اعمال می‌شود |
| GET | `/articles/{id}/publish-package` | خروجی آماده کپی برای انتشار دستی: `{blog, title, content, anchor, url, category}` (فقط اگر `human_approved=true`) |
| GET | `/articles/{id}/status-history` | *(جدید)* تاریخچه‌ی کامل عبور این مقاله از ۶ مرحله (از `content_status_history`) |

## Internal Link Suggestions *(جدید — Internal Link Suggestion Agent)*

ماژول مستقل از پایپ‌لاین گست‌پست — برای پیشنهاد ساختار لینک‌دهی داخلیِ خودِ سایت پروژه (بین صفحات ثبت‌شده در Target Pages)، **نه** لینک درون مقالات لینک‌سازی خارجی.

| Method | Path | توضیح |
|---|---|---|
| POST | `/projects/{id}/analyze-internal-links` | اجرای `ai_job(type=internal_link_suggestion)` روی همه‌ی `target_pages` این پروژه |
| GET | `/projects/{id}/internal-link-suggestions` | لیست پیشنهادها (فیلتر `status`) |
| POST | `/internal-link-suggestions/{id}/apply` | علامت‌گذاری به‌عنوان اعمال‌شده (پیاده‌سازی واقعی روی سایت خارج از این ابزار است) |
| POST | `/internal-link-suggestions/{id}/dismiss` | رد پیشنهاد |

## Jobs (وضعیت پردازش AI)

| Method | Path | توضیح |
|---|---|---|
| GET | `/jobs/{id}` | وضعیت/نتیجه یک job (برای polling از فرانت) |
| GET | `/jobs?status=pending&job_type=article_write` | لیست jobها (dashboard مانیتورینگ داخلی) |

## Reports

| Method | Path | توضیح |
|---|---|---|
| GET | `/projects/{id}/report` | خلاصه کل پروژه: تعداد لینک ساخته‌شده، صفحات تقویت‌شده |
| GET | `/campaigns/{id}/report` | گزارش کمپین: Anchor Distribution واقعی، لیست URLهای منتشرشده، نرخ موفقیت audit |
| GET | `/campaigns/{id}/pipeline-stats` | *(جدید)* میانگین زمان توقف در هر یک از ۶ مرحله (bottleneck analysis)، محاسبه‌شده از `content_status_history` |

## نمونه Payload — ایجاد کمپین

```json
POST /api/v1/campaigns
{
  "project_id": 1,
  "target_page_id": 5,
  "name": "AEB - Dairy Industry Links",
  "total_links_target": 20,
  "blog_count": 10,
  "duration_days": 60
}
```

## نمونه Payload — پاسخ Job در حال اجرا

```json
GET /api/v1/jobs/42
{
  "id": 42,
  "job_type": "article_write",
  "status": "success",
  "reference_table": "content_briefs",
  "reference_id": 7,
  "tokens_used": 3120,
  "cost_estimate": 0.045,
  "output_payload": { "article_id": 88 }
}
```

## نمونه Payload — تعریف Link Placement Rule سطح کمپین

```json
POST /api/v1/link-placement-rules
{
  "scope": "campaign",
  "scope_id": 12,
  "anchor_distribution": { "exact": 25, "partial": 40, "semantic": 20, "brand": 15 },
  "link_position_max_words": 150,
  "max_outbound_links": 1,
  "max_links_per_blog_per_month": 2,
  "min_days_between_links_same_target": 3
}
```

## نمونه Payload — تأیید نهایی مقاله (Human Approval Layer)

```json
POST /api/v1/articles/88/approve
{
  "note": "متن و لینک بررسی شد، آماده انتشار است."
}
```
```json
Response
{
  "article_id": 88,
  "human_approved": true,
  "human_approved_by": 3,
  "human_approved_at": "2026-09-14T10:22:00Z",
  "approval_record_id": 501
}
```

## نمونه Payload — تعریف Project Knowledge Base

```json
PUT /api/v1/projects/1/knowledge-base
{
  "brand_name": "AEB Water",
  "brand_voice_tone": "تخصصی، غیررسمی، مبتنی بر داده و مهندسی",
  "target_audience": "مدیران فنی صنایع غذایی و دارویی",
  "industry_context": "تصفیه فاضلاب صنعتی، استانداردهای BOD/COD",
  "forbidden_words": ["ادعای درمانی", "بهترین در ایران"],
  "mandatory_points": ["اشاره به استانداردهای زیست‌محیطی در صورت مرتبط بودن"]
}
```
