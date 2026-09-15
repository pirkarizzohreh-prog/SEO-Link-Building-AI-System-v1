# API — Sprint 1 + 2 + 3 (Backend + Database, Auth, AI Agents)

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

**Deliberately not yet in Sprint 3**: SEO audit execution (`POST
/articles/{id}/audit`) + the `reports` router — Sprint 4; Playwright
publish automation — Sprint 5. The Article Writer's output sits at
`articles.status=draft` until Sprint 4's auditor (or a human, manually)
moves it forward.

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
