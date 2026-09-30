# API — Sprint 1 + 2 + 3 + 4 + 5 (Backend + Database, Auth, AI Agents, SEO Audit + Reports, Automation)

FastAPI + SQLAlchemy + Alembic backend for the SEO Link Building AI Platform.
See `/docs` at the repo root for the full design (architecture, DB schema,
API spec, AI workflow).

## What's in Sprint 1 (Backend + Database)

- All 25 tables from `docs/DATABASE_SCHEMA.md`, as SQLAlchemy models +
  one Alembic migration (`alembic/versions/`).
- CRUD REST endpoints for every resource that doesn't require an
  authenticated user or an AI call: Projects, Project Knowledge Base,
  Content Templates & Prompt Templates (with version history), Target
  Pages, Keywords, SERP Snapshots, Competitors & Competitor Pages,
  Content Gaps, Anchors (+ live distribution vs. the resolved target
  ratio), Link Placement Rules (+ campaign→project→global resolution),
  Blog Platforms, Campaigns, Topics, Content Briefs, Articles (+ nested
  SEO audit results / publications, read-only), Internal Link
  Suggestions, and a read-only view of `ai_jobs`.

## What's in Sprint 2 (Auth)

- JWT auth: `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
  (`app/core/security.py`, `app/api/deps.py`). Stateless — a refresh
  token is just a longer-lived JWT with `type=refresh`, no revocation
  list; acceptable for an internal MVP, revisit before this matters.
- **Every other endpoint now requires `Authorization: Bearer <token>`**,
  wired once at the router-group level (`app/api/v1/router.py`), not by
  editing each Sprint 1 router.
- `POST /users` / `GET /users` / `PUT /users/{id}` (admin-only) — an
  addendum to `docs/API_SPEC.md`'s Auth section, needed to actually
  onboard a team once login is required everywhere. There's no public
  registration; create the first admin out-of-band:

  ```bash
  python -m app.cli create-admin --name "Ada" --email ada@example.com --password "..."
  # or, via Docker Compose:
  docker compose exec api python -m app.cli create-admin --name "Ada" --email ada@example.com --password "..."
  ```
- The Human Approval Layer's actual write paths, previously stubbed out
  in Sprint 1 (`app/services/approval_service.py` +
  `app/services/status_history_service.py`, the only code allowed to
  write `approvals` / `content_status_history` / `Article.human_approved`):
  - `POST /topics/{id}/approve` and `/reject`
  - `POST /content-briefs/{id}/approve`
  - `POST /articles/{id}/approve`, `/reject`, `/publish` (hard `409` gate
    if the article isn't `human_approved` yet — the same check the
    Sprint 5 automated publish path will reuse) and
    `GET /articles/{id}/publish-package` (`app/services/publication_service.py`
    picks a suggested blog platform)
- `docs/API_SPEC.md`'s Link Placement Rules ratio and anchor-position
  rule are now actually resolved (`app/services/rules_service.py`) rather
  than only documented.

## What's in Sprint 3 (AI Agents)

- `app/ai/providers/`: the `BaseLLMClient` interface (`app/ai/providers/
  base.py`) plus `OpenAIClient` and `ClaudeClient` — OpenAI is picked
  first if `OPENAI_API_KEY` is set, else `ANTHROPIC_API_KEY`
  (`app/ai/providers/factory.py`), per docs/ARCHITECTURE.md. Every agent
  is written against `BaseLLMClient`, never a concrete SDK, so tests
  inject `tests/fake_llm_client.py` instead of calling a real API.
- `app/jobs/worker.py`: the actual MVP job queue worker — `python -m
  app.jobs.worker` polls `ai_jobs` for `status='pending'` (`FOR UPDATE
  SKIP LOCKED` on Postgres) and runs them one at a time. Exits with a
  clear error if neither API key is configured, rather than crashing
  obscurely; `docker-compose.yml`'s `worker` service just keeps retrying
  it via `restart: unless-stopped`, which is a fine way to represent
  "not configured yet" for a compose stack.
- `app/jobs/handlers.py`: dispatches a job to its agent
  (`app/ai/agents/*.py` — one per docs/AI_WORKFLOW.md agent, sharing the
  `keyword_agent` / `topic_agent` / `competitor_intel_agent` /
  `brief_agent` / `writer_agent` / `internal_link_agent` split from
  `docs/PROJECT_STRUCTURE.md`), owns the job's running→success/failed
  lifecycle, and chains `keyword_intel` → `topic_gen` automatically on
  success (docs/AI_WORKFLOW.md's "زنجیره‌ی خودکار") — every step after
  that needs a human approval in between, so nothing else auto-chains.
- Prompts are DB-backed (`app/ai/prompts_service.py`): the `.md` files in
  `app/ai/prompts/` are seed content only, lazily registered as
  `prompt_templates` version 1 the first time an agent runs with none
  active yet; from then on the DB row (editable via
  `POST /prompt-templates`, no redeploy) is the source of truth, exactly
  as docs/AI_WORKFLOW.md specifies.
- `app/services/anchor_service.py` (new): `pick_next_anchor` actually
  implements the anchor-distribution logic the Article Writer needs —
  Sprint 1/2 only had the read-only `/anchors/distribution` view; both
  now share `compute_actual_counts`.
- New enqueue-only endpoints (each just creates an `ai_jobs` row and
  returns `202` immediately — no LLM call in the request path, per
  docs/ARCHITECTURE.md's reason for having a job queue at all):
  `POST /campaigns/{id}/start` (+ `/pause`), `POST /topics/{id}/
  generate-brief`, `POST /content-briefs/{id}/generate-article`,
  `POST /competitor-pages/{id}/analyze`, `POST /projects/{id}/
  analyze-internal-links`. Each enforces the precondition
  docs/API_SPEC.md implies (e.g. a topic must be `selected` before a
  brief job can run for it) with a `409` otherwise.
- `app/ai/safe_fetch.py`: the Competitor Intelligence agent fetches an
  arbitrary user-submitted URL server-side — a classic SSRF vector — so
  it resolves the hostname and refuses private/loopback/link-local
  addresses first. Not a hardened general-purpose fetcher (see the
  module docstring for what it doesn't cover); revisit before this tool
  is exposed beyond a trusted internal team.

**Deliberately not yet in Sprint 3**: SEO audit execution + the `reports`
router — Sprint 4 (below); Playwright publish automation — Sprint 5.

## What's in Sprint 4 (SEO Audit + Reports)

- `POST /articles/{id}/audit` (`app/api/v1/routers/articles.py`):
  enqueues a `seo_audit` job from `draft` or `needs_human_review`,
  flipping `articles.status → in_audit` immediately (`202`, same
  enqueue-then-poll pattern as every other AI job endpoint).
- `app/ai/agents/auditor_agent.py` — the SEO Auditor, per
  docs/AI_WORKFLOW.md ("Stage: Audit"). Runs entirely inside one job
  (not chained across separate jobs):
  - **Hard checks** (deterministic, no LLM; any failure triggers a
    retry): word count ≥ brief target, link presence, exact
    anchor/URL match, link position ≤ the resolved
    `link_position_max_words`, outbound link count ≤ the resolved
    `max_outbound_links`.
  - On a hard-check failure, the article is rewritten **in place**
    (same brief, same anchor) via `app/ai/agents/writer_agent.
    generate_draft` — factored out of the Article Writer specifically
    so both flows share one prompt-builder — with the failed checks'
    details appended to the prompt as feedback. Up to
    `auditor_agent.MAX_AUDIT_RETRIES` (2) rewrites, tracked on the new
    `articles.audit_retry_count` column; exhausting retries lands on
    `needs_human_review` instead of `reviewed`.
  - **Soft checks** (never block the pass/fail outcome or trigger a
    retry — recorded for the human reviewer only): heading structure
    vs. the brief's outline, keyword density, duplicate similarity to
    other articles on the same target page (pure-Python Jaccard
    n-gram similarity — no `pg_trgm`/Postgres-only extension needed),
    and an LLM tone/forbidden-words check seeded from
    `app/ai/prompts/seo_audit.md`.
  - Exactly one `content_status_history(stage=audit)` row is written
    per run, regardless of how many retries happened inside it — see
    the module docstring for why.
- `app/api/v1/routers/reports.py` + `app/services/report_service.py`
  (Report Manager, docs/AI_WORKFLOW.md "مرحله ۱۰", pure read-only
  aggregation — no AI involved):
  - `GET /projects/{id}/report` — total target pages/campaigns,
    published-article count, distinct target pages covered.
  - `GET /campaigns/{id}/report` — anchor distribution (resolved
    target ratio vs. actual `anchor_usage_log` counts), published
    URLs, and the audit success rate (share of audited articles that
    reached `reviewed`/`approved`/`published` rather than
    `needs_human_review`).
  - `GET /campaigns/{id}/pipeline-stats` — the Pipeline Bottleneck
    Report: average hours spent in each of the 6 stages, computed by
    walking each entity's (`topics`/`content_briefs`/`articles`)
    `content_status_history` rows in order and measuring the gap
    since the previous row (or the entity's own `created_at` for its
    first transition).
- `ArticleRead` now exposes `audit_retry_count`.

## What's in Sprint 5 (Automation)

- **Credential encryption** (`app/core/crypto.py`): `blog_platforms.
  password_encrypted` is Fernet-encrypted (not KMS — a real KMS would be
  the "غیرضروری" complexity this project explicitly avoids for a
  single-tenant internal tool). New `FERNET_KEY` setting
  (`app/core/config.py`); `POST /blog-platforms/{id}/credentials`
  (admin-only) is the *only* way to write a credential — never through
  the general `BlogPlatformCreate`/`Update` schemas. `BlogPlatformRead`
  exposes `has_automation_credentials` (a bool) instead of the secret
  itself.
- **`app/automation/`** — Playwright publishers, per docs/
  PROJECT_STRUCTURE.md's `automation/publishers/base_publisher.py` /
  `<platform>_publisher.py` split, behind one `BasePublisher` interface
  (mirrors `app/ai/providers/base.py`'s `BaseLLMClient` shape on
  purpose — same reason: swappable, and tests inject `tests/
  fake_publisher.py` instead of a real browser).
  - **Deviation from docs/PROJECT_STRUCTURE.md**: that doc sketches
    `automation/` as a top-level directory, kept separate in case it
    ever needs a different language/runtime. We use Playwright's Python
    bindings (same language as the rest of the backend), so there's no
    runtime split to justify a second top-level package and Docker
    build context; `app/automation/` ships in the existing `worker`
    image (same image as `api`) with zero build changes. See the
    module's own docstring for the full reasoning.
  - `wordpress_publisher.py`: the only publisher implemented — logs
    into a self-hosted WordPress's classic editor (**"Text"/raw-HTML
    mode, not Gutenberg** — see its docstring for why), fills
    title/content, publishes, and reads back the live URL.
  - `markdown_to_html.py`: converts an article's Markdown body (H2/H3 +
    `[text](url)` links — the only syntax the Article Writer prompt
    ever produces) into the HTML WordPress's Text-mode editor expects.
    Stdlib-only, same spirit as `app/ai/html_extract.py`.
- `app/ai/agents/publish_agent.py` — the `publish` job. No LLM call
  (docs/AI_WORKFLOW.md marks Publisher "بدون LLM"); resolves its
  publisher via `app.automation.publishers.factory.get_publisher()`
  (monkeypatched in tests, same pattern as `competitor_intel_agent`'s
  `fetch_html`). Repeats the `human_approved` check `POST /articles/
  {id}/publish-automated` already made — defense in depth, per docs/
  AI_WORKFLOW.md and docs/DATABASE_SCHEMA.md's hard rule that this gate
  lives at the service layer, not one call site. A failed attempt
  records a `publications(status=failed)` row and re-raises so
  `ai_jobs.error_message` captures it — automation failures are never
  silent.
- `POST /articles/{id}/publish-automated` (new, separate from the
  existing manual `POST /articles/{id}/publish` — kept as two endpoints
  rather than overloading one, so each has one predictable response
  shape) enqueues the job after checking `human_approved` and that the
  chosen (or suggested) blog platform actually has credentials
  configured.
- `GET /articles/{id}/status-history` — a docs/API_SPEC.md endpoint from
  Sprint 2 that nothing had implemented yet; added here since Sprint 5's
  own testing needed real visibility into an article's stage
  transitions anyway.
- Dockerfile: `playwright install --with-deps chromium`, since `worker`
  shares `api`'s image.

**Known limitations** (see the code's own docstrings for detail): only
one publisher (self-hosted WordPress, classic editor); no SSRF guard on
`blog_platforms.url`/`login_url` the way `safe_fetch.py` guards
Competitor Intelligence's fetches — these are admin-configured trusted
infrastructure, not user-submitted URLs an AI agent processes, so the
threat model differs; best-effort category selection (skipped, not
failed, if the theme's category checkbox label doesn't match).

## Running locally

### With Docker Compose (from the repo root)

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000 · Swagger UI: http://localhost:8000/docs

### Without Docker

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only needed to actually run the publish job

# point at a local Postgres (see docker-compose.yml for the expected user/db)
export DATABASE_URL="postgresql+psycopg2://seo:seo@localhost:5432/seo_link_building"

alembic upgrade head
uvicorn app.main:app --reload
```

To actually process AI jobs (in a second terminal, same env vars, plus a
real API key — nothing works without one):

```bash
export OPENAI_API_KEY="sk-..."   # or ANTHROPIC_API_KEY
python -m app.jobs.worker
```

## Tests

The test suite runs against an in-memory SQLite database (no Postgres
needed) via `tests/conftest.py`. `client`/`editor_client` fixtures are
pre-authenticated (as an admin/editor respectively); use `_raw_client`
for auth-flow tests that need to control the `Authorization` header
themselves.

```bash
cd apps/api
pytest
```

## Migrations

```bash
# after changing a model in app/models/
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Note: Postgres native ENUM types aren't dropped by `op.drop_table()` —
if you hand-write a downgrade for a migration that adds enum columns,
drop the corresponding `sa.Enum(name=...)` types explicitly too (see the
initial migration for the pattern), or a downgrade→upgrade cycle will
fail with "type already exists".
