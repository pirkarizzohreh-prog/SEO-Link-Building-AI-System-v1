"""Import every model so SQLAlchemy's mapper registry can resolve the
string-based relationship() references used throughout this package, and
so `Base.metadata` (used by Alembic autogenerate and by the test suite)
sees every table.
"""

from app.models.ai_job import AiJob
from app.models.anchor import Anchor
from app.models.anchor_usage_log import AnchorUsageLog
from app.models.approval import Approval
from app.models.article import Article
from app.models.blog_platform import BlogPlatform
from app.models.campaign import Campaign
from app.models.competitor import Competitor
from app.models.competitor_page import CompetitorPage
from app.models.content_brief import ContentBrief
from app.models.content_gap import ContentGap
from app.models.content_status_history import ContentStatusHistory
from app.models.content_template import ContentTemplate
from app.models.internal_link_suggestion import InternalLinkSuggestion
from app.models.keyword import Keyword
from app.models.link_placement_rule import LinkPlacementRule
from app.models.project import Project
from app.models.project_knowledge_base import ProjectKnowledgeBase
from app.models.prompt_template import PromptTemplate
from app.models.publication import Publication
from app.models.seo_audit_result import SeoAuditResult
from app.models.serp_snapshot import SerpSnapshot
from app.models.target_page import TargetPage
from app.models.topic import Topic
from app.models.user import User

__all__ = [
    "AiJob",
    "Anchor",
    "AnchorUsageLog",
    "Approval",
    "Article",
    "BlogPlatform",
    "Campaign",
    "Competitor",
    "CompetitorPage",
    "ContentBrief",
    "ContentGap",
    "ContentStatusHistory",
    "ContentTemplate",
    "InternalLinkSuggestion",
    "Keyword",
    "LinkPlacementRule",
    "Project",
    "ProjectKnowledgeBase",
    "PromptTemplate",
    "Publication",
    "SeoAuditResult",
    "SerpSnapshot",
    "TargetPage",
    "Topic",
    "User",
]
