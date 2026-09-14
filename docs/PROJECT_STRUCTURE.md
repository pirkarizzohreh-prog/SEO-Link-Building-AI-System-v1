# ساختار فولدر پروژه (طراحی — هنوز اسکفولد نشده)

> طبق درخواست، در این مرحله فقط **طراحی** ساختار ارائه می‌شود؛ ایجاد فایل‌ها و کدنویسی واقعی بعد از تأیید شما انجام خواهد شد.

## استراتژی: Monorepo با دو اپ (`api` و `web`) + مستندات + اتوماسیون فاز ۲

```
seo-link-building-ai-system/
├── apps/
│   ├── api/                          # Backend — FastAPI
│   │   ├── app/
│   │   │   ├── main.py               # entrypoint FastAPI
│   │   │   ├── core/
│   │   │   │   ├── config.py         # تنظیمات env (Pydantic Settings)
│   │   │   │   └── security.py       # JWT, password hashing
│   │   │   ├── db/
│   │   │   │   ├── base.py           # Base declarative + session
│   │   │   │   └── session.py
│   │   │   ├── models/               # مدل‌های SQLAlchemy (۱ فایل به ازای هر جدول دیتابیس)
│   │   │   │   ├── project.py
│   │   │   │   ├── project_knowledge_base.py   # جدید
│   │   │   │   ├── content_template.py         # جدید (دور سوم)
│   │   │   │   ├── prompt_template.py          # جدید (دور سوم)
│   │   │   │   ├── target_page.py
│   │   │   │   ├── keyword.py
│   │   │   │   ├── serp_snapshot.py            # جدید (دور سوم)
│   │   │   │   ├── competitor.py               # جدید
│   │   │   │   ├── competitor_page.py          # جدید
│   │   │   │   ├── content_gap.py              # جدید
│   │   │   │   ├── anchor.py
│   │   │   │   ├── anchor_usage_log.py
│   │   │   │   ├── link_placement_rule.py      # جدید (دور سوم)
│   │   │   │   ├── blog_platform.py
│   │   │   │   ├── campaign.py
│   │   │   │   ├── topic.py
│   │   │   │   ├── content_brief.py            # جدید
│   │   │   │   ├── article.py
│   │   │   │   ├── seo_audit_result.py
│   │   │   │   ├── publication.py
│   │   │   │   ├── approval.py                 # جدید (دور سوم)
│   │   │   │   ├── content_status_history.py   # جدید (دور سوم)
│   │   │   │   ├── internal_link_suggestion.py # جدید
│   │   │   │   └── ai_job.py
│   │   │   ├── schemas/              # Pydantic schemas (Request/Response)
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       ├── router.py     # aggregator
│   │   │   │       └── routers/
│   │   │   │           ├── auth.py
│   │   │   │           ├── projects.py
│   │   │   │           ├── knowledge_base.py       # جدید
│   │   │   │           ├── content_templates.py    # جدید (دور سوم)
│   │   │   │           ├── prompt_templates.py     # جدید (دور سوم)
│   │   │   │           ├── target_pages.py
│   │   │   │           ├── serp_snapshots.py       # جدید (دور سوم)
│   │   │   │           ├── competitors.py          # جدید
│   │   │   │           ├── content_gaps.py         # جدید
│   │   │   │           ├── anchors.py
│   │   │   │           ├── link_placement_rules.py # جدید (دور سوم)
│   │   │   │           ├── blog_platforms.py
│   │   │   │           ├── campaigns.py
│   │   │   │           ├── topics.py
│   │   │   │           ├── content_briefs.py       # جدید
│   │   │   │           ├── articles.py             # شامل approve/reject/publish (Human Approval Layer)
│   │   │   │           ├── internal_links.py       # جدید
│   │   │   │           ├── jobs.py
│   │   │   │           └── reports.py
│   │   │   ├── services/             # منطق کسب‌وکار، جدا از routerها
│   │   │   │   ├── campaign_service.py
│   │   │   │   ├── rules_service.py        # جدید (دور سوم) — resolve نسبت انکر/محدودیت‌ها (campaign→project→global)
│   │   │   │   ├── anchor_service.py       # پیکرشکنی: پیش‌فرض ۳۰/۳۵/۲۰/۱۵ از rules_service خوانده می‌شود
│   │   │   │   ├── seo_audit_service.py    # چک‌های دترمینیستیک
│   │   │   │   ├── competitor_fetch_service.py  # جدید — fetch HTTP ساده صفحات رقیب
│   │   │   │   ├── approval_service.py     # جدید (دور سوم) — تنها نقطه‌ی مجاز نوشتن روی human_approved
│   │   │   │   ├── status_history_service.py  # جدید (دور سوم) — ثبت انتقال بین ۶ مرحله
│   │   │   │   └── report_service.py       # شامل pipeline-stats (bottleneck analysis)
│   │   │   ├── ai/
│   │   │   │   ├── providers/
│   │   │   │   │   ├── base.py           # Interface LLMProvider
│   │   │   │   │   ├── openai_provider.py
│   │   │   │   │   └── claude_provider.py
│   │   │   │   ├── agents/
│   │   │   │   │   ├── competitor_intel_agent.py   # جدید
│   │   │   │   │   ├── keyword_agent.py
│   │   │   │   │   ├── topic_agent.py
│   │   │   │   │   ├── brief_agent.py              # جدید
│   │   │   │   │   ├── writer_agent.py
│   │   │   │   │   ├── auditor_agent.py
│   │   │   │   │   └── internal_link_agent.py      # جدید
│   │   │   │   └── prompts/              # seed اولیه‌ی prompt_templates (منبع حقیقت در runtime: DB)
│   │   │   │       ├── _kb_context.md          # جدید — partial مشترک Knowledge Base
│   │   │   │       ├── competitor_analysis.md  # جدید
│   │   │   │       ├── keyword_intel.md
│   │   │   │       ├── topic_generator.md
│   │   │   │       ├── brief_generation.md     # جدید
│   │   │   │       ├── article_writer.md
│   │   │   │       ├── seo_audit.md
│   │   │   │       └── internal_link_suggestion.md  # جدید
│   │   │   ├── jobs/
│   │   │   │   ├── worker.py          # polling loop روی ai_jobs
│   │   │   │   └── handlers.py        # نگاشت job_type (۹ نوع) → اجرای agent مربوطه
│   │   │   └── utils/
│   │   ├── alembic/                   # migrations
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── web/                           # Frontend — Next.js
│       ├── app/
│       │   ├── (dashboard)/
│       │   │   ├── projects/
│       │   │   │   └── [id]/knowledge-base/   # جدید — فرم تنظیمات برند/لحن/قوانین
│       │   │   ├── content-templates/         # جدید (دور سوم) — مدیریت انواع محتوا
│       │   │   ├── prompt-templates/          # جدید (دور سوم) — ویرایش/نسخه‌بندی پرامپت‌ها
│       │   │   ├── competitors/               # جدید — رقبا + Content Gaps + SERP Snapshots
│       │   │   ├── link-placement-rules/      # جدید (دور سوم) — قوانین کمپین (نسبت انکر و…)
│       │   │   ├── campaigns/
│       │   │   ├── content-briefs/            # جدید — بازبینی/تأیید بریف قبل از نگارش
│       │   │   ├── articles/          # صفحه‌ی Review/Approve مقالات (شامل گیت Human Approval)
│       │   │   ├── internal-links/            # جدید — گزارش پیشنهادهای لینک داخلی
│       │   │   ├── blog-platforms/
│       │   │   └── reports/                   # شامل Pipeline Bottleneck Report (۶ مرحله)
│       │   └── login/
│       ├── components/
│       ├── lib/
│       │   └── api-client.ts
│       ├── styles/
│       ├── package.json
│       └── Dockerfile
│
├── automation/                        # فاز ۲ — اتوماسیون انتشار
│   ├── publishers/
│   │   ├── base_publisher.py
│   │   └── <platform>_publisher.py    # هر وبلاگ یک اسکریپت Playwright
│   └── playwright.config.ts
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── PROJECT_STRUCTURE.md
│   ├── API_SPEC.md
│   └── AI_WORKFLOW.md
│
├── docker-compose.yml                 # postgres + api + worker + web
├── .env.example
└── README.md
```

## نکات طراحی ساختار

- **جدایی `services/` از `api/routers/`**: routerها فقط validate + فراخوانی service؛ منطق کسب‌وکار (مثل قانون توزیع انکر) در تست‌های واحد جدا قابل تست است.
- **`ai/providers/`** پشت یک Interface مشترک: تعویض OpenAI ↔ Claude فقط تغییر config است، نه تغییر کد agentها.
- **`ai/prompts/` جدا از کد پایتون**: تغییر پرامپت (که در این نوع ابزار زیاد اتفاق می‌افتد) نیازی به دیپلوی مجدد backend ندارد اگر بعداً از فایل/DB لود شود.
- **`jobs/worker.py` مستقل از `main.py`**: API و Worker دو پروسه جدا هستند (در `docker-compose` دو container) تا کندی تولید مقاله، پاسخ‌دهی API را کند نکند.
- **`automation/` جدا از `apps/api`**: چون فاز ۲ است و ممکن است حتی زبان/اجرای متفاوتی داشته باشد (مثلاً یک سرویس Node+Playwright جدا)، از ابتدا مرزبندی شده تا به مونولیت اصلی وابستگی سنگین اضافه نشود.
