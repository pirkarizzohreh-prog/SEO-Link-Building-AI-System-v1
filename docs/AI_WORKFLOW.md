# Workflow تولید مقاله با AI

## نگاشت ایجنت‌ها به معماری فنی (به‌روزرسانی‌شده — دور سوم)

| Agent / ماژول | پیاده‌سازی فنی | نوع اجرا |
|---|---|---|
| Project Knowledge Base | جدول `project_knowledge_base` — context ثابت تزریق‌شده به پرامپت همه‌ی ایجنت‌های محتوایی | بدون فراخوانی مستقل؛ data injection |
| Content Templates / Prompt Templates *(جدید)* | جداول `content_templates` + `prompt_templates` — تعریف اسکلت محتوا و نسخه‌بندی پرامپت هر ایجنت | بدون فراخوانی مستقل؛ config/versioning لایه |
| SERP Snapshot Storage *(جدید)* | جدول `serp_snapshots` — ورودی خام Competitor Intelligence | بدون LLM (ثبت داده؛ در MVP دستی) |
| Competitor Intelligence Agent | تحلیل صفحات رقیب (از روی `serp_snapshots`/URL دستی) + استخراج Content Gap | فراخوانی LLM (+ fetch HTTP ساده) |
| SEO Strategist (سند اولیه) | ترکیب `Keyword Intelligence Agent` + `Topic Generator Agent` | فراخوانی LLM |
| Link Placement Rules *(جدید)* | جدول `link_placement_rules` — resolve نسبت انکر/محدودیت‌ها به‌جای مقدار hardcode | بدون LLM؛ منطق سرویس (`rules_service.resolve()`) |
| Content Brief Generator | Topic + Keywords + Content Gaps + Knowledge Base + Content Template → بریف ساختاریافته | فراخوانی LLM (خروجی JSON) |
| Content Writer (سند اولیه) | `Article Writer Agent` — از روی Content Brief + قوانین resolve‌شده از Link Placement Rules می‌نویسد | فراخوانی LLM |
| SEO Reviewer (سند اولیه) | `SEO Auditor Agent` = چک‌های دترمینیستیک (کد) + یک چک کیفی سبک با LLM | ترکیبی |
| Human Approval Layer *(جدید)* | جدول `approvals` — گیت اجباری قبل از publish؛ **هیچ کد/ایجنتی نمی‌تواند دور بزند** | بدون LLM؛ اجباری در سرویس |
| Internal Link Suggestion Agent | تحلیل مستقل صفحات `target_pages` برای پیشنهاد لینک‌دهی داخلی سایت | فراخوانی LLM؛ مستقل از پایپ‌لاین گست‌پست |
| Publisher (سند اولیه) | `Publication Manager` (MVP: دستی / فاز۲: Playwright) — هر دو مسیر پشت گیت `human_approved=true` | بدون LLM |
| Report Manager (سند اولیه) | Aggregation با SQL، از جمله `content_status_history` برای bottleneck analysis | بدون LLM |

## Advanced Content Status Workflow — نگاشت ۶ مرحله به Enumهای پایگاه‌داده

سند شما این ۶ مرحله را خواسته: **Idea → Brief → Writing → Audit → Human Review → Published**. این مراحل یک enum جدید و مجزا در دیتابیس نیستند (برای جلوگیری از دوباره‌کاری با enumهای موجود هر جدول)، بلکه یک **برچسب یکدست** هستند که در `content_status_history.stage` ثبت می‌شوند و در UI/گزارش استفاده می‌شوند:

| Stage (سند شما) | جدول مسئول | مقادیر status متناظر |
|---|---|---|
| **Idea** | `topics` | `suggested`, `selected`, `rejected` |
| **Brief** | `content_briefs` | `draft`, `approved` |
| **Writing** | `articles` | `draft` (در حال نگارش/بازنویسی) |
| **Audit** | `articles` | `in_audit` *(جدید)*, `reviewed`, `needs_human_review` |
| **Human Review** | `articles` | همان `reviewed`/`needs_human_review` تا لحظه‌ی `POST /articles/{id}/approve` (که `human_approved=true` می‌کند) |
| **Published** | `articles` + `publications` | `approved` → `published` |

هر انتقال بین این مراحل (چه با AI چه با کاربر) یک ردیف در `content_status_history` ثبت می‌کند؛ این یعنی برای هر مقاله می‌توان دقیقاً دید چه زمانی از Idea به Brief رفته، چقدر در Audit مانده، و غیره (endpoint: `GET /articles/{id}/status-history` و گزارش تجمیعی `GET /campaigns/{id}/pipeline-stats`).

## دیاگرام State Machine کامل (به‌روزرسانی‌شده — دور سوم)

```
 project_knowledge_base + content_templates + prompt_templates(active) + link_placement_rules
        │  (context/config ثابت — بدون فراخوانی مستقل)
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: IDEA                                                                │
│                                                                             │
│  [رقبا ثبت شدند - اختیاری]                                                 │
│         │                                                                  │
│         ▼                                                                  │
│  serp_snapshots (manual/api) ──▶ competitor_analysis (ai_job)              │
│         │                              │                                   │
│         ▼                              ▼                                   │
│  competitor_pages[]              content_gaps[]                            │
│                                         │                                   │
│  [campaign.start] ─▶ keyword_intel (ai_job) ─▶ keywords[]                  │
│         │                                                                  │
│         ▼                                                                  │
│  topic_gen (ai_job، ورودی += content_gaps) ─▶ topics[status=suggested]     │
│         │                                                                  │
│         ▼                                                                  │
│  (تأیید انسانی) ─▶ POST /topics/{id}/approve                              │
│         │             └─▶ approvals(topic_selection) + status_history      │
│         ▼                                                                  │
│  topics[status=selected]  ══════════════════ STAGE: IDEA تمام شد ══════════│
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: BRIEF                                                               │
│  brief_generation (ai_job، ورودی += content_template انتخابی) ─▶           │
│         content_briefs[status=draft]                                       │
│         │                                                                  │
│         ▼                                                                  │
│  (تأیید انسانی اختیاری/auto-approve) ─▶ approvals(brief_approval)          │
│         │                                                                  │
│         ▼                                                                  │
│  content_briefs[status=approved]  ═══════════ STAGE: BRIEF تمام شد ═══════│
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: WRITING                                                             │
│  link_placement_rules.resolve(campaign) ─▶ anchor_service.pick_next_anchor │
│         │                                                                  │
│         ▼                                                                  │
│  article_write (ai_job، ورودی = content_brief + قوانین resolve‌شده) ─▶     │
│         articles[status=draft]  ═══════════ STAGE: WRITING تمام شد ═══════│
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: AUDIT                                                               │
│  articles[status=in_audit] ─▶ seo_audit (ai_job) ──┬─▶ PASS               │
│         │                                          │                       │
│         │                                          └─▶ articles[reviewed]  │
│         └─▶ FAIL ─▶ retry (max 2، فیدبک به پرامپت) ─▶ برگشت به WRITING     │
│                          │                                                 │
│                          └─▶ بعد از ۲ شکست ─▶ articles[needs_human_review] │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: HUMAN REVIEW                                                        │
│  کاربر محتوا را می‌بیند (reviewed یا needs_human_review)                    │
│         │                                                                  │
│         ▼                                                                  │
│  POST /articles/{id}/approve  ◀── تنها راه ست‌شدن human_approved=true      │
│         └─▶ approvals(pre_publish, decided_by=<user>) + status_history     │
│         │                                                                  │
│         ▼                                                                  │
│  articles[human_approved=true]  ═══ STAGE: HUMAN REVIEW تمام شد ══════════│
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ STAGE: PUBLISHED                                                           │
│  POST /articles/{id}/publish                                              │
│    ├─ چک اجباری: human_approved == true  ── وگرنه 409 Conflict            │
│    ├─ MVP: ثبت دستی published_url                                         │
│    └─ فاز۲: ai_job(type=publish) → Playwright bot (همان چک را اجرا می‌کند) │
│         │                                                                  │
│         ▼                                                                  │
│  articles[status=published] + publications[record]                        │
└───────────────────────────────────────────────────────────────────────────┘


 ── مسیر مستقل و موازی (بدون اتصال به ۶ مرحله بالا) ──
 [کاربر: "Analyze Internal Links" روی یک پروژه]
        │
        ▼
 internal_link_suggestion (ai_job) ──▶ internal_link_suggestions[] (گزارش/دشبورد جدا)
```

## مرحله به مرحله

### مرحله ۰ — پیش‌نیازهای Config (بدون فراخوانی مستقل)

- **Project Knowledge Base**: تنظیم یک‌بار در سطح پروژه (برند/لحن/مخاطب/قوانین ممنوعه-الزامی)؛ به پرامپت Topic Generator، Content Brief Generator، Article Writer و SEO Auditor تزریق می‌شود.
- **Content Templates**: کاربر (یا پیش‌فرض سیستم) یک تمپلیت محتوا برای `page_type` مربوطه انتخاب می‌کند (مثلاً «How-To») که اسکلت پایه‌ی Content Brief Generator می‌شود. اختیاری — بدون انتخاب، Brief Generator اسکلت را از صفر می‌سازد.
- **Prompt Templates**: هر ایجنت (`keyword_intel`, `topic_gen`, `competitor_analysis`, `brief_generation`, `article_write`, `seo_audit`, `internal_link_suggestion`) نسخه‌ی فعال خودش را از `prompt_templates` می‌خواند؛ تغییر پرامپت = ثبت نسخه‌ی جدید در dashboard، بدون دیپلوی.
- **Link Placement Rules**: قبل از هر انتخاب انکر یا نگارش، سرویس `rules_service.resolve(campaign_id)` قانون مؤثر (campaign → project → global) را برمی‌گرداند: نسبت انکر، حداکثر موقعیت لینک، حداکثر لینک خروجی، محدودیت انتشار در هر وبلاگ.

### مرحله ۱ — SERP Snapshot + Competitor Intelligence Agent *(اختیاری، مستقل از زمان‌بندی کمپین)*
- **ورودی**: یک `serp_snapshot` (ثبت دستی نتایج جست‌وجوی یک کلیدواژه در MVP) یا مستقیماً URL رقیب.
- **پردازش**: از `serp_snapshot.results` یا URL دستی، صفحات رقیب در `competitor_pages` ثبت می‌شوند (با `source_serp_snapshot_id` در صورت وجود) → fetch محتوای صفحه (HTTP ساده) → LLM ساختار هدینگ و کلیدواژه‌ها را استخراج و با `keywords`/مقالات قبلیِ همان `target_page` مقایسه می‌کند.
- **خروجی**: `content_gaps` با `gap_type` مشخص (`topic`/`keyword`/`heading`).
- **پرامپت (خلاصه)**:
  > «متن و ساختار هدینگ صفحه‌ی رقیب زیر را با کلیدواژه‌ها و موضوعات فعلی ما مقایسه کن. موضوعات یا زیرعنوان‌هایی که رقیب پوشش داده و ما نداده‌ایم را به‌صورت JSON لیست کن.»
- **مصرف‌کننده‌ی خروجی**: مرحله ۳ (Topic Generator) و مرحله ۴ (Content Brief Generator).
- **ارزش SERP Snapshot جدا از یک fetch یک‌باره**: چون نتایج به‌صورت تاریخ‌دار (`fetched_at`) ذخیره می‌شوند، می‌توان بعداً (مثلاً هر ۳ ماه) دوباره اسنپ‌شات گرفت و روند تغییر رتبه‌بندی رقبا را دید — بدون این جدول، هر تحلیل رقیب جای قبلی را پاک می‌کرد.

### مرحله ۲ — Keyword Intelligence Agent
- **ورودی**: `target_page` (title, url, main_keyword).
- **خروجی**: `keywords` (type=`related`/`semantic`).
- بدون تغییر نسبت به نسخه قبلی طراحی.

### مرحله ۳ — Topic Generator Agent
- **ورودی**: `main_keyword` + `related topics` + `content_gaps` وضعیت `new` + `project_knowledge_base`.
- **قانون سخت‌گیرانه (سند اولیه، بدون تغییر)**: موضوعات نباید تبلیغاتی باشند.
- **خروجی**: N موضوع در `topics` (`status=suggested`)؛ gap مصرف‌شده → `used_in_topic`.
- **تأیید انسانی → Stage Idea تمام می‌شود**: `POST /topics/{id}/approve` هم‌زمان یک `approvals(approval_type=topic_selection)` و یک `content_status_history(stage=idea)` ثبت می‌کند.

### مرحله ۴ — Content Brief Generator *(بین Topic و Article Writer — Stage: Brief)*
- **هدف**: قبل از نگارش کامل مقاله (پرهزینه‌ترین فراخوانی LLM)، بریف ساختاریافته تولید شود — کاهش retry ممیزی و افزایش یکدستی.
- **ورودی**: `topic` تأییدشده + `keywords` + `content_gaps` مرتبط + `project_knowledge_base` + (اختیاری) `content_template` انتخاب‌شده به‌عنوان اسکلت پایه.
- **خروجی**: `content_briefs` شامل `outline`، `target_word_count`، `keywords_to_include`، `must_include_points`، `tone`، و در صورت استفاده از تمپلیت، `content_template_id`.
- **پرامپت (نسخه‌ی فعال از `prompt_templates` با `agent_type=brief_generation`، خلاصه)**:
  > «برای موضوع «{topic.title}» یک بریف محتوایی ساختاریافته بساز. اگر یک اسکلت پایه (Content Template) داده شده، از آن به‌عنوان چارچوب استفاده کن؛ در غیر این صورت از صفر بساز. خروجی JSON طبق اسکیمای مشخص.»
- **تأیید انسانی (اختیاری در MVP، auto-approve پیکربندی‌پذیر در سطح کمپین) → Stage Brief تمام می‌شود**: `POST /content-briefs/{id}/approve` یک `approvals(brief_approval)` ثبت می‌کند.

### مرحله ۵ — Article Writer Agent *(Stage: Writing)*
- **پیش‌نیاز انکر و قوانین**: `rules_service.resolve(campaign_id)` قوانین مؤثر (نسبت انکر، حداکثر موقعیت لینک، حداکثر تعداد لینک خروجی) را برمی‌گرداند؛ سپس `anchor_service.pick_next_anchor(target_page_id, rules)` انکر بعدی را طبق آن نسبت انتخاب می‌کند (نه دیگر hardcode ۳۰/۳۵/۲۰/۱۵؛ آن فقط **مقدار پیش‌فرض global** است).
- **پرامپت اصلی (نسخه‌ی فعال `prompt_templates` با `agent_type=article_write`، خلاصه)**:

  ```
  تو یک متخصص SEO و نویسنده تخصصی هستی.
  یک مقاله برای وبلاگ خارجی بنویس.

  [بلوک project_knowledge_base در صورت وجود]

  از بریف محتوایی زیر پیروی کن:
  {content_brief.outline}
  کلیدواژه‌های لازم: {content_brief.keywords_to_include}
  نکات الزامی: {content_brief.must_include_points}

  لینک هدف: {target_page.url}
  انکر متن (باید دقیقاً همین باشد): {anchor.anchor_text}

  قوانین (resolve‌شده از link_placement_rules این کمپین):
  - حداقل {content_brief.target_word_count} کلمه
  - لینک در {rules.link_position_max_words} کلمه اول
  - حداکثر {rules.max_outbound_links} لینک خروجی
  - لحن انسانی، ساختار H2/H3 دقیقاً طبق بریف
  - بدون تبلیغات مستقیم، انکر طبیعی، عدم keyword stuffing

  خروجی را به‌صورت Markdown با H2/H3 مشخص بازگردان.
  ```
- **خروجی**: `articles[status=draft]` با `content_brief_id` تنظیم‌شده؛ `ai_jobs` رکورد مربوطه `prompt_template_id`/`prompt_template_version` را برای ردیابی ذخیره می‌کند.
- در صورت retry بعد از شکست audit، فیدبک auditor به همین پرامپت اضافه می‌شود (برگشت به همین Stage، نه Stage قبلی).

### مرحله ۶ — SEO Auditor Agent *(Stage: Audit)*

هنگام شروع، `articles.status → in_audit`. چک‌های دترمینیستیک (بدون LLM):

| چک | روش |
|---|---|
| تعداد کلمات ≥ حد بریف | شمارش کلمات |
| وجود لینک | regex |
| صحت URL/Anchor | تطبیق دقیق |
| موقعیت لینک ≤ `rules.link_position_max_words` | offset متن (نه دیگر عدد ثابت ۱۰۰) |
| تعداد لینک خروجی ≤ `rules.max_outbound_links` | شمارش |
| وجود H2/H3 مطابق outline بریف | مقایسه با `content_brief.outline` (هشدار نرم اگر انحراف زیاد) |
| Keyword Density معقول | نسبت تکرار |
| عدم شباهت به مقالات قبلی | trigram similarity (MVP) |
| لحن هماهنگ با Knowledge Base | چک کیفی LLM با `forbidden_words` |

منطق pass/fail و retry بدون تغییر (حداکثر ۲ retry خودکار → `needs_human_review`)؛ نتیجه‌ی نهایی `articles.status → reviewed` یا `needs_human_review` و یک ردیف `content_status_history(stage=audit)` ثبت می‌شود.

### مرحله ۷ — Human Approval Layer *(جدید، Stage: Human Review — گیت اجباری)*

- کاربر مقاله (`reviewed` یا `needs_human_review`) را در Dashboard می‌بیند و محتوا/انکر/لینک را بازبینی می‌کند.
- **تنها راه** ست‌شدن `articles.human_approved = true` فراخوانی `POST /articles/{id}/approve` توسط یک کاربر لاگین‌شده است — این هم‌زمان یک رکورد `approvals(approval_type=pre_publish, decision=approved, decided_by=<user_id>)` ثبت می‌کند.
- **هیچ Agent یا ai_job** (نه SEO Auditor، نه هیچ فرآیند خودکار دیگری) اجازه‌ی نوشتن روی `human_approved` را ندارد — این قانون در سطح Service Layer اجرا می‌شود (نه فقط UI)، طوری که حتی فراخوانی مستقیم API هم بدون رکورد `approvals` معتبر رد می‌شود.
- رد مقاله (`POST /articles/{id}/reject`) هم یک `approvals(decision=rejected)` ثبت می‌کند تا تاریخچه‌ی کامل تصمیمات انسانی همیشه قابل بازیابی باشد.

### مرحله ۸ — Publication Manager *(Stage: Published)*

**پیش از هر چیز**: `POST /articles/{id}/publish` (چه مسیر دستی چه خودکار) ابتدا `human_approved == true` بودن را چک می‌کند؛ در غیر این صورت **بدون استثنا** `409 Conflict` برمی‌گرداند — این یعنی حتی یک باگ در Worker یا یک صف کار خراب هم نمی‌تواند مقاله‌ای را بدون تأیید انسانی منتشر کند.

**نسخه اول (MVP - Manual):**
1. سیستم یک `blog_platform` مناسب را از بین وبلاگ‌های `active` پیشنهاد می‌دهد (با احترام به `rules.max_links_per_blog_per_month`).
2. `GET /articles/{id}/publish-package` خروجی آماده می‌دهد.
3. کاربر دستی منتشر می‌کند و `POST /articles/{id}/publish` را با URL نهایی صدا می‌زند → `publications` + `articles.status=published`.

**نسخه دوم (Phase 2 - Automated):**
- `ai_job(type=publish)` → Playwright script (در `automation/publishers/`) — همان چک `human_approved` را قبل از اجرا تکرار می‌کند (defense in depth، نه اعتماد صرف به لایه بالادست).
- خطاهای اتوماسیون هرگز silent fail نیستند؛ در `ai_jobs.error_message` ثبت و flag می‌شوند.

### مرحله ۹ — Internal Link Suggestion Agent *(مسیر مستقل، خارج از ۶ مرحله بالا)*
بدون تغییر نسبت به نسخه قبلی طراحی: تحلیل `target_pages` یک پروژه، تولید `internal_link_suggestions`، هرگز به `articles` گست‌پست متصل نمی‌شود (قانون «فقط یک لینک خروجی» دست‌نخورده می‌ماند).

### مرحله ۱۰ — Report Manager (بدون AI)
علاوه بر گزارش‌های قبلی (تعداد لینک، Anchor Distribution واقعی در برابر resolve‌شده از `link_placement_rules`، لیست URLها)، اکنون یک گزارش جدید اضافه می‌شود:
- **Pipeline Bottleneck Report** (`GET /campaigns/{id}/pipeline-stats`): میانگین زمان توقف هر مقاله در هر یک از ۶ Stage، محاسبه‌شده از `content_status_history` — مشخص می‌کند مثلاً «اکثر مقالات ۲ روز در Human Review معطل می‌مانند» تا تیم بتواند گلوگاه واقعی فرآیند را ببیند.

## اصول طراحی پرامپت (به‌روزرسانی‌شده — دور سوم)

- پرامپت‌ها اکنون **منبع اصلی‌شان دیتابیس است** (`prompt_templates`, نسخه‌بندی‌شده)، نه فقط فایل‌های استاتیک `ai/prompts/*.md`. فایل‌های `.md` همچنان به‌عنوان **seed اولیه** (مقدار پیش‌فرض هنگام اولین migration) نگه داشته می‌شوند، اما در runtime همیشه نسخه‌ی `is_active=true` از دیتابیس خوانده می‌شود.
- بلوک `project_knowledge_base` همچنان یک partial مشترک (`_kb_context.md`، به‌عنوان seed) است که در `template_text` هر `prompt_templates` مربوطه include می‌شود.
- خروجی همه‌ی ایجنت‌های ساختاریافته (keywords، topics، content_gaps، content_briefs، internal_link_suggestions) باید **JSON اسکیمای مشخص** بگیرند.
- هر فراخوانی LLM از طریق `LLMProvider.generate(prompt, schema=None)` رد می‌شود؛ `ai_jobs` علاوه بر token/cost، اکنون `prompt_template_id`+`prompt_template_version` را هم ثبت می‌کند — یعنی همیشه می‌توان گفت «این مقاله دقیقاً با کدام نسخه‌ی پرامپت نوشته شده».
- Retry با فیدبک: بدون تغییر.
- **قانون تفکیک اختیارات (Separation of Concerns) نهایی**: تولید محتوا (AI) و تأیید انتشار (انسان) دو مسیر کاملاً جدا در کدند. `ai_jobs` هرگز به `approvals` یا `articles.human_approved` نمی‌نویسد؛ فقط `services/approval_service.py` (که فقط از یک endpoint احراز‌هویت‌شده صدا زده می‌شود) این اجازه را دارد. این جداسازی در Code Review هم قابل چک است: هر PR که به `human_approved` می‌نویسد و از مسیر `ai/` می‌آید، رد می‌شود.
