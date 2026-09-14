# SEO Link Building AI Platform

ابزار داخلی برای اتوماسیون تولید، مدیریت و انتشار مقالات لینک‌سازی SEO برای چندین پروژه.

> این نسخه از مخزن فعلاً فقط شامل **طراحی (Design)** است؛ کدنویسی هنوز آغاز نشده و پس از تأیید این طراحی انجام خواهد شد.

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
