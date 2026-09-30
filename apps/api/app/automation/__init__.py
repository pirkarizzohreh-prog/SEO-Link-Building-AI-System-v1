"""Publication automation — docs/AI_WORKFLOW.md ("Stage: Published",
نسخه دوم/Phase 2) and docs/PROJECT_STRUCTURE.md.

docs/PROJECT_STRUCTURE.md sketches this as a top-level `automation/`
directory, kept outside `apps/api` in case it ever needs a different
language/runtime (its own note: "ممکن است حتی زبان/اجرای متفاوتی داشته
باشد"). We use Playwright's Python bindings — same language as the rest of
the backend — so there's no such runtime split to justify a separate
top-level package and its own Docker build context; keeping it as
`app/automation/` lets the existing `worker` service (same image as `api`,
see docker-compose.yml) run it with zero build changes. Revisit only if a
future publisher genuinely needs a different runtime.
"""
