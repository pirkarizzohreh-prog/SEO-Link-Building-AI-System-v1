# SEO Link Building AI Platform

ابزار داخلی برای اتوماسیون تولید، مدیریت و انتشار مقالات لینک‌سازی SEO برای چندین پروژه.

## وضعیت توسعه

| Sprint | محتوا | وضعیت |
|---|---|---|
| **1** | Backend + Database | ✅ انجام شد — [`apps/api`](apps/api) (FastAPI + SQLAlchemy + Alembic، ۲۵ جدول، CRUD کامل غیر از موارد وابسته به Auth/AI) |
| **2** | Authentication + Dashboard | ✅ انجام شد — JWT auth + Human Approval Layer در [`apps/api`](apps/api)، داشبورد Next.js در [`apps/web`](apps/web) |
| **3** | AI Agents | ✅ انجام شد — LLM Provider abstraction (OpenAI/Claude)، Job Worker، ۶ ایجنت (Keyword/Topic/Competitor/Brief/Writer/Internal Link) در [`apps/api`](apps/api)؛ دکمه‌های تولید با AI + صفحه AI Jobs در [`apps/web`](apps/web) |
| **4** | SEO Audit + Reports | ✅ انجام شد — SEO Auditor Agent (چک‌های سخت + نرم + retry خودکار) و Report Manager (`/projects/{id}/report`، `/campaigns/{id}/report`، `/campaigns/{id}/pipeline-stats`) در [`apps/api`](apps/api)؛ دکمه اجرای ممیزی + صفحه گزارش‌ها در [`apps/web`](apps/web) |
| **5** | Automation | ✅ انجام شد — رمزنگاری اطلاعات ورود وبلاگ (Fernet)، اتوماسیون انتشار با Playwright (`app/automation/`, `publish_agent`) و `GET /articles/{id}/status-history` در [`apps/api`](apps/api)؛ فرم اطلاعات ورود + دکمه انتشار خودکار در [`apps/web`](apps/web) |

جزئیات مرزبندی دقیق هر Sprint (چه چیزی الان پیاده شده و چه چیزی عمداً بعداً می‌آید) در [`apps/api/README.md`](apps/api/README.md) و [`apps/web/README.md`](apps/web/README.md).

## مستندات طراحی

| سند | محتوا |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | سند نیازمندی اولیه (خلاصه‌شده) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | معماری MVP و Tech Stack انتخابی + دلایل |
| [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | طراحی کامل جداول PostgreSQL |
| [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) | ساختار پیشنهادی فولدر پروژه |
| [`docs/API_SPEC.md`](docs/API_SPEC.md) | لیست کامل REST APIها |
| [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md) | Workflow دقیق تولید مقاله با ایجنت‌های AI + پرامپت‌ها |

## خلاصه یک‌خطی معماری

Next.js Dashboard → FastAPI (Service Layer + AI Agent Layer) → PostgreSQL، با یک Job Worker ساده (بدون Redis در MVP) برای اجرای async فراخوانی‌های OpenAI/Claude، و اتوماسیون انتشار با Playwright به‌عنوان فاز ۲.

جزئیات کامل در [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## پایپ‌لاین AI (تأییدشده، نسخه سوم طراحی — نهایی قبل از Scaffold)

**Advanced Content Status Workflow — ۶ مرحله**: `Idea → Brief → Writing → Audit → Human Review → Published`

```
Project Knowledge Base + Content Templates + Prompt Templates + Link Placement Rules
        │  (context/config ثابت)
        │
[Idea]   SERP Snapshot → Competitor Intelligence → Content Gaps
             │
         Keyword Intelligence → Topic Generator (با Content Gaps) → تأیید انسانی
             │
[Brief]  Content Brief Generator (اسکلت از Content Template) → تأیید انسانی
             │
[Writing] Article Writer (طبق Link Placement Rules resolve‌شده)
             │
[Audit]  SEO Auditor (retry خودکار در صورت شکست)
             │
[Human Review]  گیت اجباری Human Approval Layer — هیچ مسیر خودکاری این گیت را دور نمی‌زند
             │
[Published]  Publication Manager (MVP: دستی / فاز۲: Playwright)

── مستقل ──
Internal Link Suggestion Agent  (لینک‌دهی داخلی سایت، جدا از مقالات لینک‌سازی)
```

جزئیات کامل در [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md).
