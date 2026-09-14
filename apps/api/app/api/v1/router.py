from fastapi import APIRouter

from app.api.v1.routers import (
    anchors,
    articles,
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

api_router.include_router(projects.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(content_templates.content_templates_router)
api_router.include_router(content_templates.prompt_templates_router)
api_router.include_router(target_pages.router)
api_router.include_router(serp_snapshots.router)
api_router.include_router(competitors.router)
api_router.include_router(anchors.router)
api_router.include_router(link_placement_rules.router)
api_router.include_router(blog_platforms.router)
api_router.include_router(campaigns.router)
api_router.include_router(topics.router)
api_router.include_router(content_briefs.router)
api_router.include_router(articles.router)
api_router.include_router(internal_links.router)
api_router.include_router(jobs.router)

# NOTE: an `auth` router (Sprint 2) and a `reports` router (Sprint 4) are
# intentionally not included yet — see docs/AI_WORKFLOW.md and the sprint
# plan for what each one depends on.
