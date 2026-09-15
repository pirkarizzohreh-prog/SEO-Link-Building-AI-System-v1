# API — Sprint 1 + 2 (Backend + Database, Auth)

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

**Deliberately not yet in Sprint 2** (see `NOTE:` comments in the
relevant routers): anything that triggers an LLM call
(`/campaigns/{id}/start`, `/topics/{id}/generate-brief`,
`/competitor-pages/{id}/analyze`, ...) and the job worker — Sprint 3; SEO
audit execution + the `reports` router — Sprint 4; Playwright publish
automation — Sprint 5.

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
