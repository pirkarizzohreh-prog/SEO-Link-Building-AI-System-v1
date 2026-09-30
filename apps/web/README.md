# Web — Sprint 2 + 3 + 4 + 5 (Dashboard, AI Agents UI, SEO Audit + Reports UI, Automation UI)

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

## What's in Sprint 3 (AI Agents UI)

- Campaign detail: a **"شروع خودکار با AI"** button (`POST /campaigns/{id}/
  start`) that kicks off Stage: Idea, plus pause/resume.
- The Content Brief panel (under each `selected` topic) gets a
  **"تولید بریف با AI"** button alongside the manual form; it polls
  `GET /topics/{id}/brief` every 3s until the worker finishes (see
  `useBrief`'s `poll` option in `lib/hooks.ts`) rather than needing a
  manual refresh.
- Once a topic's brief is `approved`, a **"تولید مقاله با AI"** row
  appears in the campaign's Articles section.
- Competitors page: register a competitor page against a target page and
  **"تحلیل با AI"** it; a Content Gaps card lists what the analysis found
  for a chosen target page.
- Internal Links page: **"تحلیل لینک‌های داخلی با AI"**.
- A new **AI Jobs** page (`/jobs`) — the queue's read-only view, polling
  every 3s while anything is `pending`/`running` (`useAiJobs`'s
  `refetchInterval`) so job status is visible without digging through
  the API directly.

**Deliberately thin / not in Sprint 3:**
- The dashboard has no visibility into `ai_jobs.error_message` inline
  next to the button that triggered it — only on the Jobs page. Failed
  jobs are visible, just not contextually linked yet.
- No SSR data fetching: every `(dashboard)` page is a Client Component
  using React Query. Reasonable for an internal, login-gated tool with no
  SEO surface of its own; revisit if that stops being true.

## What's in Sprint 4 (SEO Audit + Reports UI)

- Article detail page (`/articles/[id]`): an **"اجرای ممیزی SEO"** button
  (`POST /articles/{id}/audit`), shown while the article is `draft` or
  `needs_human_review`. `useArticle` polls every 3s while the status is
  `in_audit` (same pattern as `useBrief`'s polling), so the page reflects
  pass/retry/`needs_human_review` automatically once the SEO Auditor job
  finishes — no manual refresh. The SEO audit results card now shows
  every hard + soft check the auditor ran (docs/AI_WORKFLOW.md), and the
  header shows how many times the auditor auto-rewrote the article
  (`article.audit_retry_count`).
- A real **Reports page** (`/reports`), replacing the Sprint 3
  placeholder: pick a project for its summary (target pages, campaigns,
  links built, pages covered), then a campaign for its report (anchor
  distribution target vs. actual, audit success rate, published URLs)
  and the **Pipeline Bottleneck Report** (average hours spent in each of
  the 6 stages, from `GET /campaigns/{id}/pipeline-stats`).

## What's in Sprint 5 (Automation UI)

- Blog Platforms page: an **"اتوماسیون"** column (تنظیم‌شده/تنظیم‌نشده)
  and an admin-only **"تنظیم اطلاعات ورود"** button opening a modal for
  username/password/login URL — `POST /blog-platforms/{id}/credentials`.
  The password field is never pre-filled or echoed back; the page only
  ever learns whether credentials exist (`has_automation_credentials`),
  never their value.
- Article detail page: a second, **"انتشار خودکار (Playwright)"** section
  next to the existing manual publish form, letting an approved article
  be published via `POST /articles/{id}/publish-automated` (optionally
  picking a specific blog; platforms without credentials are shown
  disabled in the dropdown). Since the actual Playwright run happens in
  the background worker, this only enqueues the job and points to the
  Jobs page / this article's own history for the result — there's no
  synchronous "in progress" state to poll the way `/audit` has.
- A new **"تاریخچه مراحل (Pipeline)"** card on the article page —
  `GET /articles/{id}/status-history` — showing every stage transition
  this article has been through (Idea → ... → Published), who/what made
  it (AI or a named user) and when; this is what makes an automated
  publish's `approved → published` transition visible without leaving
  the page.

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
