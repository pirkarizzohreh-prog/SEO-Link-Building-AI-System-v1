# Web — Sprint 2 (Dashboard)

Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 dashboard for the
SEO Link Building AI Platform. See `/docs` at the repo root for the full
design; `apps/api/README.md` for what the backend it talks to actually
does (and deliberately doesn't yet).

> **Stack note**: `docs/ARCHITECTURE.md` specifies "Next.js 14". At
> scaffold time, Next 14.2.35 (the latest 14.x patch) carried several
> disclosed CVEs — including one critical — with no fix inside the 14.x
> line, only from 16.x onward. This app ships on Next 16 + React 19
> instead; the substantive architecture decision (App Router, TypeScript,
> Tailwind) is unchanged, only the major version pin.

## What's in Sprint 2

- Login (`/login`), backed by `apps/api`'s `/auth/*` endpoints. Tokens are
  stored in `localStorage` and attached by `lib/api-client.ts`, which also
  retries once through `/auth/refresh` on a 401 before giving up and
  redirecting to `/login`.
- A `(dashboard)` route group (`src/app/(dashboard)/layout.tsx`) that
  redirects to `/login` when there's no authenticated user, wrapping
  every other page in a sidebar + topbar shell.
- CRUD screens for every Sprint 1 resource: Projects (+ Project Knowledge
  Base, Target Pages, Anchors, Keywords, anchor distribution), Campaigns,
  Blog Platforms, Content Templates, Competitors.
- The **Human Approval Layer** UI end to end: Topics (approve/reject,
  inline under each campaign), a Content Brief panel that appears under
  each `selected` topic (create manually, then approve), and the Article
  detail page (`/articles/[id]`) — approve/reject, the publish-package
  preview, and the manual publish form. The publish form is
  hard-disabled (not just hidden) until the article is `human_approved`,
  matching the backend's `409` gate.
- Admin-only user management (`/users`), since there's no public
  registration — see `apps/api/README.md`'s `create-admin` CLI for the
  very first account.

**Deliberately thin / not in Sprint 2:**
- No dedicated Content Brief page — briefs are created/approved inline
  from the campaign's topic list is *not* wired up (only the API supports
  it); approving a brief today means calling `POST /content-briefs/{id}/
  approve` directly. Worth a small page once Sprint 3 actually generates
  briefs to review.
- Competitors/Internal Links pages are list + create only (no analyze/
  apply-suggestion generation UI) — those actions are AI jobs, Sprint 3.
- Reports is a placeholder — Sprint 4.
- No SSR data fetching: every `(dashboard)` page is a Client Component
  using React Query. Reasonable for an internal, login-gated tool with no
  SEO surface of its own; revisit if that stops being true.

## Known trade-off: tokens in `localStorage`

Documented in `lib/api-client.ts`. An XSS bug in this app (or in a
dependency) could exfiltrate a session; httpOnly cookies set by a
backend-for-frontend would not be readable by injected script. Acceptable
for an internal MVP behind a login wall; revisit before this app is ever
exposed to less-trusted users or user-generated content.

## Running locally

### With Docker Compose (from the repo root)

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: http://localhost:3000 · API: http://localhost:8000/docs

Create the first admin user (see `apps/api/README.md`):

```bash
docker compose exec api python -m app.cli create-admin \
  --name "Ada" --email ada@example.com --password "a-real-password"
```

### Without Docker

```bash
cd apps/web
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to localhost:8000
npm install
npm run dev
```

## Checks

```bash
npm run lint
npm run build   # also runs the TypeScript compiler
```

There is no frontend test suite yet (no browser-automation tooling was
available at scaffold time); `apps/api`'s pytest suite covers the
approval-flow logic this UI drives.
