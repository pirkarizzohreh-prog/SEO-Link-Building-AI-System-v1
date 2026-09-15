from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.routers import (
    anchors,
    articles,
    auth,
    blog_platforms,
    campaigns,
    competitors,
    content_briefs,
    content_templates,
    internal_links,
    jobs,
    knowledge_base,
    link_placement_rules,
    projects,
    serp_snapshots,
    target_pages,
    topics,
)

api_router = APIRouter()

# Public (login, refresh) + self-protected (/auth/me, /users/*) — see
# app/api/v1/routers/auth.py for the per-route dependencies.
api_router.include_router(auth.router)
api_router.include_router(auth.users_router)

# Everything else requires a valid access token, per docs/API_SPEC.md
# ("Auth: Authorization: Bearer <JWT> (به‌جز /auth/login)"). Applying the
# dependency once here — rather than on each of the 15 routers below — is
# what actually turns on auth for Sprint 1's endpoints; nothing in those
# router files changed.
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(projects.router)
protected_router.include_router(knowledge_base.router)
protected_router.include_router(content_templates.content_templates_router)
protected_router.include_router(content_templates.prompt_templates_router)
protected_router.include_router(target_pages.router)
protected_router.include_router(serp_snapshots.router)
protected_router.include_router(competitors.router)
protected_router.include_router(anchors.router)
protected_router.include_router(link_placement_rules.router)
protected_router.include_router(blog_platforms.router)
protected_router.include_router(campaigns.router)
protected_router.include_router(topics.router)
protected_router.include_router(content_briefs.router)
protected_router.include_router(articles.router)
protected_router.include_router(internal_links.router)
protected_router.include_router(jobs.router)

api_router.include_router(protected_router)

# NOTE: a `reports` router is intentionally not included yet — Sprint 4.
