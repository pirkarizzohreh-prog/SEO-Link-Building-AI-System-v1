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
│   │   │   │   ├── target_page.py
│   │   │   │   ├── keyword.py
│   │   │   │   ├── anchor.py
│   │   │   │   ├── blog_platform.py
│   │   │   │   ├── campaign.py
│   │   │   │   ├── topic.py
│   │   │   │   ├── article.py
│   │   │   │   ├── seo_audit_result.py
│   │   │   │   ├── publication.py
│   │   │   │   └── ai_job.py
│   │   │   ├── schemas/              # Pydantic schemas (Request/Response)
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       ├── router.py     # aggregator
│   │   │   │       └── routers/
│   │   │   │           ├── auth.py
│   │   │   │           ├── projects.py
│   │   │   │           ├── target_pages.py
│   │   │   │           ├── anchors.py
│   │   │   │           ├── blog_platforms.py
│   │   │   │           ├── campaigns.py
│   │   │   │           ├── topics.py
│   │   │   │           ├── articles.py
│   │   │   │           ├── jobs.py
│   │   │   │           └── reports.py
│   │   │   ├── services/             # منطق کسب‌وکار، جدا از routerها
│   │   │   │   ├── campaign_service.py
│   │   │   │   ├── anchor_service.py     # منطق توزیع ۳۰/۳۵/۲۰/۱۵
│   │   │   │   ├── seo_audit_service.py  # چک‌های دترمینیستیک
│   │   │   │   └── report_service.py
│   │   │   ├── ai/
│   │   │   │   ├── providers/
│   │   │   │   │   ├── base.py           # Interface LLMProvider
│   │   │   │   │   ├── openai_provider.py
│   │   │   │   │   └── claude_provider.py
│   │   │   │   ├── agents/
│   │   │   │   │   ├── keyword_agent.py
│   │   │   │   │   ├── topic_agent.py
│   │   │   │   │   ├── writer_agent.py
│   │   │   │   │   └── auditor_agent.py
│   │   │   │   └── prompts/              # قالب پرامپت‌ها (Jinja2 / .md)
│   │   │   │       ├── keyword_intel.md
│   │   │   │       ├── topic_generator.md
│   │   │   │       ├── article_writer.md
│   │   │   │       └── seo_audit.md
│   │   │   ├── jobs/
│   │   │   │   ├── worker.py          # polling loop روی ai_jobs
│   │   │   │   └── handlers.py        # نگاشت job_type → اجرای agent مربوطه
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
│       │   │   ├── campaigns/
│       │   │   ├── articles/          # صفحه‌ی Review/Approve مقالات
│       │   │   ├── blog-platforms/
│       │   │   └── reports/
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
