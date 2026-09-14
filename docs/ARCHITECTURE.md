# معماری MVP و Tech Stack — SEO Link Building AI Platform

## ۱. تصمیم معماری کلی

سند اولیه دو مسیر پیشنهاد داده بود: (الف) MVP بدون‌کد با Airtable+n8n، (ب) اپلیکیشن کامل با FastAPI+PostgreSQL+Next.js.

از آنجا که الان درخواست DB Schema، ساختار فولدر و API مشخص شده، مسیر انتخابی **"اپ کدنویسی‌شده سبک"** است — نه یک SaaS پیچیده چندمستأجری (multi-tenant enterprise)، بلکه یک **مونولیت ساده و تمیز** که:

- به‌راحتی توسط یک یا دو نفر قابل توسعه و نگهداری باشد.
- بدون زیرساخت اضافه (بدون Kubernetes، بدون microservices، بدون message broker سنگین) اجرا شود.
- مسیر ارتقا به نسخه‌های بعدی (چند کاربره، اتوماسیون انتشار با Playwright، چند‌پروژه‌ای در مقیاس بزرگ‌تر) را نبندد.

### دیاگرام معماری (High-Level)

```
┌──────────────────────┐        HTTPS/JSON        ┌───────────────────────────┐
│   Next.js Dashboard   │  ───────────────────────▶ │        FastAPI (REST)     │
│  (Projects, Campaigns,│  ◀─────────────────────── │  apps/api                 │
│   Articles Review UI) │                            │                           │
└──────────────────────┘                            │  ┌─────────────────────┐  │
                                                      │  │   Service Layer     │  │
                                                      │  │ (Campaign, Anchor,  │  │
                                                      │  │  SEO Audit, Report) │  │
                                                      │  └─────────┬───────────┘  │
                                                      │            │              │
                                                      │  ┌─────────▼───────────┐  │
                                                      │  │   AI Agent Layer     │  │
                                                      │  │ (Keyword/Topic/      │  │
                                                      │  │  Writer/Auditor)     │  │
                                                      │  └─────────┬───────────┘  │
                                                      └────────────┼──────────────┘
                                                                   │
                          ┌────────────────────────────────────────┼───────────────┐
                          │                                        │               │
                 ┌────────▼────────┐                     ┌─────────▼─────────┐     │
                 │   PostgreSQL     │                     │  LLM Providers     │     │
                 │ (source of truth)│                     │ OpenAI / Claude    │     │
                 └──────────────────┘                     └────────────────────┘     │
                                                                                       │
                          ┌────────────────────────────────────────────────────────────┘
                          │
                 ┌────────▼─────────┐
                 │  Job Worker       │  ← polling روی جدول ai_jobs (بدون Redis در MVP)
                 │ (async AI calls)  │
                 └────────┬──────────┘
                          │  (فاز ۲)
                 ┌────────▼──────────┐
                 │ Playwright Bots    │  ← Publication Automation
                 │ (per blog platform)│
                 └────────────────────┘
```

### چرا مونولیت به‌جای Microservices؟

- تعداد کاربران داخلی محدود است (تیم لینک‌سازی داخلی، نه هزاران کاربر همزمان).
- فرآیند اصلی (تولید مقاله) I/O-bound روی API مدل‌های LLM است، نه CPU-bound؛ نیازی به مقیاس‌پذیری افقی پیچیده نیست.
- توسعه، دیباگ و دیپلوی یک سرویس واحد بسیار سریع‌تر از هماهنگی چند سرویس است.
- در صورت رشد (چند تیم، چند مشتری SaaS)، لایه Service Layer از قبل مرزبندی منطقی دارد و می‌تواند به سرویس‌های مجزا شکسته شود.

### چرا صف کار (Job Queue) و نه فراخوانی همزمان (Sync) به LLM؟

تولید مقاله (Article Writer) و ممیزی SEO چند ثانیه تا حدود یک دقیقه طول می‌کشد. اگر این فراخوانی‌ها را داخل request همزمان HTTP انجام دهیم:
- ریسک timeout در مرورگر/پراکسی وجود دارد.
- امکان تولید موازی چند مقاله برای چند کمپین از بین می‌رود.
- Retry و لاگ‌گیری دقیق هزینه/توکن سخت می‌شود.

**راه‌حل MVP:** یک جدول `ai_jobs` در PostgreSQL به‌عنوان صف کار ساده + یک پروسه Worker پایتون که با polling (هر چند ثانیه) کارهای `pending` را برمی‌دارد و اجرا می‌کند. این یعنی **بدون نیاز به Redis/RabbitMQ** در MVP. وقتی حجم کار بالا رفت (مثلاً صدها مقاله همزمان)، همین جدول به‌سادگی به Celery+Redis یا RQ مهاجرت می‌کند چون قرارداد (job type, payload, status) از قبل مشخص است.

## ۲. Tech Stack انتخابی

| لایه | انتخاب | دلیل |
|------|--------|------|
| Backend Framework | **Python 3.11+ / FastAPI** | مطابق پیشنهاد کارفرما؛ async native، مستندسازی خودکار OpenAPI، مناسب فراخوانی API های LLM |
| ORM / Migration | **SQLAlchemy 2.0 + Alembic** | استاندارد صنعتی پایتون، migration نسخه‌بندی‌شده |
| Validation | **Pydantic v2** | هماهنگ با FastAPI، اعتبارسنجی ورودی/خروجی API |
| Database | **PostgreSQL 15+** | مطابق پیشنهاد کارفرما؛ پشتیبانی از JSONB (برای payload های AI)، Full Text Search داخلی برای چک شباهت مقالات |
| Job Queue (MVP) | **جدول Postgres + Worker Python ساده** (بدون Redis) | کاهش زیرساخت اولیه؛ قابل ارتقا به Celery/RQ در فاز بعد |
| Job Queue (Scale-up) | Celery + Redis *(فاز ۲+)* | وقتی تعداد کمپین/مقاله همزمان بالا رفت |
| AI Layer | **OpenAI API (GPT-4o/4.1)** به‌عنوان اصلی، **Claude API** به‌عنوان جایگزین/fallback | پشت یک Interface واحد (`LLMProvider`) طراحی می‌شود تا تعویض یا A/B تست مدل‌ها راحت باشد |
| Frontend | **Next.js 14 (App Router) + TypeScript + TailwindCSS + shadcn/ui** | مطابق پیشنهاد کارفرما؛ برای dashboard مدیریت پروژه/کمپین/مقاله |
| Data Fetching (FE) | React Query (TanStack Query) | مدیریت state سرور، polling وضعیت job ها |
| Auth | JWT ساده (FastAPI OAuth2PasswordBearer) با نقش‌های `admin` / `editor` | ابزار داخلی تیمی؛ نیازی به OAuth پیچیده نیست ولی چندکاربره بودن از ابتدا لحاظ شده |
| Automation انتشار *(فاز ۲)* | **Playwright** (به‌جای Selenium) | API مدرن‌تر، پایدارتر، async-friendly، هماهنگ با بقیه استک |
| Containerization | Docker + docker-compose | یک دستور برای بالا آوردن api + worker + db + web در dev/staging |
| Hosting پیشنهادی | یک VPS معمولی (Hetzner/DigitalOcean) با docker-compose | نیازی به Kubernetes/Cloud پیچیده در MVP نیست |

## ۳. محدوده دقیق MVP (نسخه اول)

### در MVP هست:
- CRUD کامل: Projects، Target Pages، Anchor Bank، Blog Platforms، Campaigns
- Pipeline خودکار AI: Keyword Intelligence → Topic Generator → Article Writer → SEO Auditor
- کنترل توزیع انکر (Exact/Partial/Semantic/Brand) به‌صورت خودکار طبق نسبت ۳۰/۳۵/۲۰/۱۵
- مرحله تأیید انسانی (Human-in-the-loop) روی موضوعات و مقالات قبل از انتشار
- **انتشار نیمه‌خودکار (Manual Publish)**: تولید بسته آماده انتشار (Title/Content/Anchor/URL/Category) برای کپی-پیست دستی در وبلاگ + ثبت وضعیت و URL نهایی
- گزارش‌گیری پایه: تعداد لینک ساخته‌شده، وضعیت هر صفحه هدف، توزیع واقعی Anchor، لیست URLهای منتشرشده
- لاگ کامل هر فراخوانی AI (پرامپت/پاسخ/توکن/هزینه تقریبی) برای شفافیت هزینه

### در MVP نیست (فاز ۲+):
- اتوماسیون کامل انتشار با Playwright (Login/Post/Publish خودکار روی وبلاگ‌ها)
- تشخیص شباهت پیشرفته مقالات با embedding vector (در MVP یک نسخه ساده‌تر با PostgreSQL Full-Text/تشابه n-gram استفاده می‌شود)
- چند‌مستأجری واقعی (Multi-tenant SaaS برای مشتریان خارجی)
- اعلان‌ها (Slack/Email notifications)، داشبورد تحلیلی پیشرفته، اتصال به Google Search Console
- مدیریت نقش‌های پیچیده و لاگ حسابرسی کامل (Audit Trail کامل UI)

این مرزبندی دقیقاً همان چیزی است که در سند اولیه هم به‌عنوان "نسخه اول" (Publication Manager) و "نسخه دوم" (اتوماسیون) از هم تفکیک شده بود.
