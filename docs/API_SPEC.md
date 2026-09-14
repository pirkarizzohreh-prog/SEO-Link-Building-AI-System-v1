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

## Anchor Bank

| Method | Path | توضیح |
|---|---|---|
| GET | `/target-pages/{id}/anchors` | لیست انکرها |
| POST | `/target-pages/{id}/anchors` | افزودن انکر |
| PUT | `/anchors/{id}` | ویرایش (مثلاً غیرفعال کردن) |
| DELETE | `/anchors/{id}` | حذف |
| GET | `/target-pages/{id}/anchors/distribution` | نسبت فعلی استفاده Exact/Partial/Semantic/Brand در برابر هدف ۳۰/۳۵/۲۰/۱۵ |

## Blog Platforms

| Method | Path | توضیح |
|---|---|---|
| GET | `/blog-platforms` | لیست |
| POST | `/blog-platforms` | افزودن وبلاگ جدید |
| PUT | `/blog-platforms/{id}` | ویرایش (وضعیت، دسته‌بندی پیش‌فرض) |
| DELETE | `/blog-platforms/{id}` | حذف |

## Campaigns

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns` | لیست (filter بر اساس project_id, status) |
| POST | `/campaigns` | ایجاد کمپین `{project_id, target_page_id, total_links_target, blog_count, duration_days}` |
| GET | `/campaigns/{id}` | جزئیات + پیشرفت (چند مقاله published از چند مورد هدف) |
| PUT | `/campaigns/{id}` | ویرایش |
| POST | `/campaigns/{id}/start` | **شروع Pipeline** → ایجاد `ai_job(type=keyword_intel)` و سپس زنجیره‌ی خودکار تا `topic_gen` |
| POST | `/campaigns/{id}/pause` | توقف موقت |

## Topics

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns/{id}/topics` | لیست موضوعات پیشنهادی |
| POST | `/topics/{id}/approve` | تأیید موضوع → آماده برای تولید بریف |
| POST | `/topics/{id}/reject` | رد موضوع |
| POST | `/topics/{id}/generate-brief` | *(جدید، جایگزین فراخوانی مستقیم generate-article)* ایجاد `ai_job(type=brief_generation)` → خروجی یک رکورد `content_briefs` |

## Content Briefs *(جدید — Content Brief Generator)*

بین Topic و Article Writer؛ خروجی این مرحله ورودی اصلی نگارش مقاله می‌شود.

| Method | Path | توضیح |
|---|---|---|
| GET | `/topics/{id}/brief` | دریافت بریف تولیدشده برای این موضوع |
| PUT | `/content-briefs/{id}` | ویرایش دستی بریف قبل از نگارش (outline، کلیدواژه‌ها، نکات الزامی) |
| POST | `/content-briefs/{id}/approve` | تأیید بریف → `status=approved` |
| POST | `/content-briefs/{id}/generate-article` | *(جایگزین مسیر قبلی)* ایجاد `ai_job(type=article_write)` با استفاده از این بریف |

## Articles

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns/{id}/articles` | لیست مقالات کمپین با فیلتر status |
| GET | `/articles/{id}` | جزئیات کامل مقاله + بریف مرتبط + نتایج SEO Audit |
| PUT | `/articles/{id}` | ویرایش دستی محتوا/عنوان (قبل از انتشار) |
| POST | `/articles/{id}/audit` | اجرای مجدد `ai_job(type=seo_audit)` |
| POST | `/articles/{id}/approve` | تغییر status → `approved` |
| POST | `/articles/{id}/reject` | تغییر status → `rejected` (+ دلیل) |
| POST | `/articles/{id}/publish` | **MVP (manual)**: ثبت `published_url` + blog_platform به‌صورت دستی؛ **فاز۲ (automated)**: trigger کردن `ai_job(type=publish)` برای Playwright bot |
| GET | `/articles/{id}/publish-package` | خروجی آماده کپی برای انتشار دستی: `{blog, title, content, anchor, url, category}` |

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
