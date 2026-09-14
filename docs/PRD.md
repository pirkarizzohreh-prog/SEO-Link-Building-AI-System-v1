# PRD — SEO Link Building AI System v1

> منبع: سند نیازمندی اولیه ارائه‌شده توسط کارفرما (فایل ورد اولیه)، بدون تغییر در محتوای اصلی، فقط پاکسازی فرمت برای نگهداری در ریپو.

## ۱. هدف سیستم

ابزاری داخلی مبتنی بر هوش مصنوعی برای مدیریت انتها‌به‌انتهای فرآیند لینک‌سازی SEO:

- مدیریت چندین پروژه SEO
- مدیریت صفحات هدف
- مدیریت انکر تکست‌ها
- پیشنهاد موضوع مقاله
- تولید مقاله تخصصی
- درج لینک و انکر به‌صورت طبیعی
- کنترل کیفیت SEO
- مدیریت وبلاگ‌های انتشار
- ثبت وضعیت لینک‌ها
- گزارش‌گیری کمپین لینک‌سازی

**هدف اصلی:** تبدیل فرآیند دستی لینک‌سازی به یک Workflow قابل تکرار و مقیاس‌پذیر.

## ۲. معماری مفهومی اولیه (از سند کارفرما)

```
Projects → Target Pages → Keyword Manager → Anchor Manager
   → Topic Generator AI → Article Writer AI → SEO Auditor AI
   → Publication Manager → Reports
```

## ۳. موجودیت‌های اصلی (نسخه خام کارفرما)

- **Projects**: project_name, website_url, industry, description, status
- **Target Pages**: project_id, title, url, main_keyword, page_type, priority
- **Blog Platforms**: نام، URL، وضعیت (+ فیلدهای آینده: username, password, login_url, category, last_publish_date)
- **Anchor Bank**: target_page, anchor, type (Exact/Partial/Semantic/Brand), usage_limit
  - قانون توزیع: به ازای هر ۲۰ لینک → Exact 30%، Partial 35%، Semantic 20%، Brand 15%
- **Articles**: title, content, target_page, anchor, status (Draft/Reviewed/Approved/Published), created_at
- **Campaigns**: نام، صفحه هدف، تعداد مقالات، مدت زمان

## ۴. Workflow (خلاصه سند اولیه)

1. تعریف کمپین (پروژه، صفحه هدف، تعداد لینک، تعداد وبلاگ)
2. **Keyword Intelligence Agent**: تحلیل صفحه هدف → Main Keyword + Related Topics
3. **Topic Generator Agent**: تولید موضوعات غیرتبلیغاتی مقاله
4. **Article Writer Agent**: نگارش مقاله با قوانین مشخص (≥۱۲۰۰ کلمه، لحن انسانی، H2/H3، بدون تبلیغ مستقیم، لینک در ۱۰۰ کلمه اول، فقط یک لینک خروجی، انکر طبیعی، بدون keyword stuffing)
5. **SEO Auditor Agent**: بررسی تعداد کلمات، وجود لینک، صحت URL/Anchor، ساختار H2/H3، طبیعی بودن متن، عدم تکرار کلیدواژه، عدم شباهت به مقالات قبلی
6. **Publication Manager**:
   - نسخه اول (MVP): تولید بسته آماده انتشار (Blog، Title، Content، Anchor، URL، Category) برای انتشار دستی
   - نسخه دوم (Phase 2): اتوماسیون با Playwright/Selenium (Login → Create Post → Insert Content/Link → Publish)

## ۵. ایجنت‌های هوش مصنوعی (سند اولیه)

| # | Agent | وظیفه |
|---|-------|-------|
| 1 | SEO Strategist | انتخاب موضوع، تعیین انکر، برنامه لینک‌سازی |
| 2 | Content Writer | تولید مقاله |
| 3 | SEO Reviewer | کنترل کیفیت |
| 4 | Publisher | انتشار |
| 5 | Report Manager | گزارش (تعداد لینک، صفحات تقویت‌شده، Anchor Distribution، URLهای منتشرشده) |

## ۶. پیشنهاد فنی اولیه کارفرما

- Backend: Python + FastAPI
- Database: PostgreSQL
- AI Layer: OpenAI API / Claude API
- Automation: n8n
- Frontend: Next.js
- **MVP سریع بدون کد**: Airtable + OpenAI API + n8n + Google Drive (به‌عنوان گزینه شروع سریع؛ در نسخه‌ی فعلی طراحی، مسیر «اپ کدنویسی‌شده سبک» انتخاب شده — نگاه کنید به `ARCHITECTURE.md`)

## ۷. مرحله بعد (طبق سند اولیه)

برای شروع توسعه ۵ سند لازم است: Database Schema، API Architecture، AI Agent Prompts، n8n/Automation Workflow، Frontend Dashboard Spec.
این مستندات در فایل‌های زیر پوشش داده شده‌اند:

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — معماری MVP و Tech Stack
- [`DATABASE_SCHEMA.md`](./DATABASE_SCHEMA.md) — طراحی کامل دیتابیس
- [`PROJECT_STRUCTURE.md`](./PROJECT_STRUCTURE.md) — ساختار فولدر پروژه
- [`API_SPEC.md`](./API_SPEC.md) — لیست کامل APIها
- [`AI_WORKFLOW.md`](./AI_WORKFLOW.md) — Workflow دقیق تولید مقاله با AI و پرامپت‌های ایجنت‌ها
