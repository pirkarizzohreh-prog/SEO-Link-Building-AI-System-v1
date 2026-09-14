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

## Target Pages

| Method | Path | توضیح |
|---|---|---|
| POST | `/projects/{project_id}/target-pages` | ایجاد صفحه هدف |
| GET | `/target-pages/{id}` | جزئیات + keywords + anchors مرتبط |
| PUT | `/target-pages/{id}` | ویرایش |
| DELETE | `/target-pages/{id}` | حذف |
| GET | `/target-pages/{id}/keywords` | لیست کلیدواژه‌ها |
| POST | `/target-pages/{id}/keywords` | افزودن دستی کلیدواژه |

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
| POST | `/topics/{id}/approve` | تأیید موضوع → آماده برای تولید مقاله |
| POST | `/topics/{id}/reject` | رد موضوع |
| POST | `/topics/{id}/generate-article` | ایجاد `ai_job(type=article_write)` برای این موضوع |

## Articles

| Method | Path | توضیح |
|---|---|---|
| GET | `/campaigns/{id}/articles` | لیست مقالات کمپین با فیلتر status |
| GET | `/articles/{id}` | جزئیات کامل مقاله + نتایج SEO Audit |
| PUT | `/articles/{id}` | ویرایش دستی محتوا/عنوان (قبل از انتشار) |
| POST | `/articles/{id}/audit` | اجرای مجدد `ai_job(type=seo_audit)` |
| POST | `/articles/{id}/approve` | تغییر status → `approved` |
| POST | `/articles/{id}/reject` | تغییر status → `rejected` (+ دلیل) |
| POST | `/articles/{id}/publish` | **MVP (manual)**: ثبت `published_url` + blog_platform به‌صورت دستی؛ **فاز۲ (automated)**: trigger کردن `ai_job(type=publish)` برای Playwright bot |
| GET | `/articles/{id}/publish-package` | خروجی آماده کپی برای انتشار دستی: `{blog, title, content, anchor, url, category}` |

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
  "reference_table": "topics",
  "reference_id": 7,
  "tokens_used": 3120,
  "cost_estimate": 0.045,
  "output_payload": { "article_id": 88 }
}
```
