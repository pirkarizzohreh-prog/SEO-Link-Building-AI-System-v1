from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.article import Article, ArticleStatus
from app.models.blog_platform import BlogPlatform
from app.models.ai_job import JobType
from app.models.content_status_history import ContentStatusHistory, PipelineStage
from app.models.publication import Publication, PublicationMethod
from app.models.publication import PublicationStatus as PubStatus
from app.models.seo_audit_result import SeoAuditResult
from app.models.user import User
from app.schemas.approval import ActionNote, PublishAutomatedRequest, PublishRequest
from app.schemas.article import (
    ArticleCreate,
    ArticleRead,
    ArticleUpdate,
    PublicationRead,
    PublishPackage,
    SeoAuditResultRead,
)
from app.schemas.content_status_history import ContentStatusHistoryRead
from app.schemas.job import AiJobRead
from app.services.approval_service import record_approval
from app.services.job_service import enqueue_job
from app.services.publication_service import suggest_blog_platform
from app.services.status_history_service import record_transition
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Articles"])
crud = CRUDBase(Article)


@router.get("/campaigns/{campaign_id}/articles", response_model=list[ArticleRead])
def list_articles(campaign_id: int, status: ArticleStatus | None = None, db: Session = Depends(get_db)):
    return crud.list(db, limit=500, campaign_id=campaign_id, status=status)


@router.post("/campaigns/{campaign_id}/articles", response_model=ArticleRead, status_code=201)
def create_article(campaign_id: int, payload: ArticleCreate, db: Session = Depends(get_db)):
    """Manual article creation (testing/fallback only) — see
    schemas.article.ArticleCreate. The Article Writer agent job (Sprint 3)
    is the normal way articles get created.
    """
    return crud.create(db, payload, campaign_id=campaign_id)


@router.get("/articles/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)):
    return crud.get(db, article_id)


@router.put("/articles/{article_id}", response_model=ArticleRead)
def update_article(article_id: int, payload: ArticleUpdate, db: Session = Depends(get_db)):
    return crud.update(db, article_id, payload)


@router.get("/articles/{article_id}/seo-audit-results", response_model=list[SeoAuditResultRead])
def list_seo_audit_results(article_id: int, db: Session = Depends(get_db)):
    crud.get(db, article_id)
    return CRUDBase(SeoAuditResult).list(db, limit=200, article_id=article_id)


@router.get("/articles/{article_id}/publications", response_model=list[PublicationRead])
def list_publications(article_id: int, db: Session = Depends(get_db)):
    crud.get(db, article_id)
    return CRUDBase(Publication).list(db, limit=50, article_id=article_id)


@router.get("/articles/{article_id}/status-history", response_model=list[ContentStatusHistoryRead])
def get_article_status_history(article_id: int, db: Session = Depends(get_db)):
    """docs/API_SPEC.md: "تاریخچه‌ی کامل عبور این مقاله از ۶ مرحله"."""
    crud.get(db, article_id)
    return (
        db.query(ContentStatusHistory)
        .filter(ContentStatusHistory.entity_table == "articles", ContentStatusHistory.entity_id == article_id)
        .order_by(ContentStatusHistory.created_at.asc())
        .all()
    )


@router.post("/articles/{article_id}/audit", response_model=AiJobRead, status_code=202)
def audit_article(article_id: int, db: Session = Depends(get_db)):
    """Enqueues the SEO Auditor (Sprint 4) — see docs/AI_WORKFLOW.md
    ("Stage: Audit"). Valid from `draft` (the normal path out of Writing)
    or `needs_human_review` (re-auditing after a manual content fix).
    """
    article = crud.get(db, article_id)
    if article.status not in (ArticleStatus.DRAFT, ArticleStatus.NEEDS_HUMAN_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Article {article_id} must be in draft or needs_human_review to run the SEO audit "
                f"(status={article.status.value})"
            ),
        )
    article.status = ArticleStatus.IN_AUDIT
    db.commit()
    return enqueue_job(db, job_type=JobType.SEO_AUDIT, reference_table="articles", reference_id=article.id)


@router.post("/articles/{article_id}/approve", response_model=ArticleRead)
def approve_article(
    article_id: int,
    payload: ActionNote = ActionNote(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human Review -> Published (pending the actual publish call).

    This is the **only** code path in the whole system allowed to set
    `human_approved = True` — see docs/AI_WORKFLOW.md ("Human Approval
    Layer") and app/models/article.py. No AI job/agent imports this
    function or writes to these columns directly.
    """
    article = crud.get(db, article_id)
    from_status = article.status.value
    article.status = ArticleStatus.APPROVED
    article.human_approved = True
    article.human_approved_by = current_user.id
    article.human_approved_at = datetime.now(timezone.utc)

    record_approval(
        db,
        entity_table="articles",
        entity_id=article.id,
        approval_type=ApprovalType.PRE_PUBLISH,
        decision=ApprovalDecision.APPROVED,
        decided_by=current_user,
        note=payload.note,
    )
    record_transition(
        db,
        entity_table="articles",
        entity_id=article.id,
        stage=PipelineStage.HUMAN_REVIEW,
        from_status=from_status,
        to_status=article.status.value,
        actor=current_user,
    )
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/reject", response_model=ArticleRead)
def reject_article(
    article_id: int,
    payload: ActionNote = ActionNote(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = crud.get(db, article_id)
    from_status = article.status.value
    article.status = ArticleStatus.REJECTED

    record_approval(
        db,
        entity_table="articles",
        entity_id=article.id,
        approval_type=ApprovalType.PRE_PUBLISH,
        decision=ApprovalDecision.REJECTED,
        decided_by=current_user,
        note=payload.note,
    )
    record_transition(
        db,
        entity_table="articles",
        entity_id=article.id,
        stage=PipelineStage.REJECTED,
        from_status=from_status,
        to_status=article.status.value,
        actor=current_user,
        note=payload.note,
    )
    db.commit()
    db.refresh(article)
    return article


@router.get("/articles/{article_id}/publish-package", response_model=PublishPackage)
def get_publish_package(article_id: int, db: Session = Depends(get_db)):
    article = crud.get(db, article_id)
    if not article.human_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Article is not human_approved yet — approve it before requesting a publish package.",
        )
    suggested = suggest_blog_platform(db)
    return PublishPackage(
        article_id=article.id,
        suggested_blog_platform_id=suggested.id if suggested else None,
        suggested_blog_platform_name=suggested.name if suggested else None,
        title=article.title,
        content=article.content,
        anchor_text=article.anchor.anchor_text,
        target_url=article.target_page.url,
        category=suggested.category_default if suggested else None,
    )


@router.post("/articles/{article_id}/publish", response_model=ArticleRead)
def publish_article(
    article_id: int,
    payload: PublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """MVP manual publish. **Hard gate**: refuses to run at all unless
    `human_approved` is already True — see docs/AI_WORKFLOW.md. The
    Sprint 5 automated (Playwright) path calls this exact same check
    before it ever launches a browser; there is no way to publish an
    article that a human hasn't approved.
    """
    article = crud.get(db, article_id)
    if not article.human_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot publish: article has not been approved via POST /articles/{id}/approve.",
        )
    if article.status == ArticleStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Article is already published.")

    blog_platform = db.get(BlogPlatform, payload.blog_platform_id)
    if blog_platform is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog platform not found")

    now = datetime.now(timezone.utc)
    publication = Publication(
        article_id=article.id,
        blog_platform_id=blog_platform.id,
        method=PublicationMethod.MANUAL,
        status=PubStatus.SUCCESS,
        published_url=payload.published_url,
        notes=payload.notes,
        published_at=now,
    )
    db.add(publication)

    article.blog_platform_id = blog_platform.id
    article.status = ArticleStatus.PUBLISHED
    article.published_url = payload.published_url
    article.published_at = now
    blog_platform.last_publish_date = now

    record_transition(
        db,
        entity_table="articles",
        entity_id=article.id,
        stage=PipelineStage.PUBLISHED,
        from_status=ArticleStatus.APPROVED.value,
        to_status=article.status.value,
        actor=current_user,
    )
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/publish-automated", response_model=AiJobRead, status_code=202)
def publish_article_automated(
    article_id: int,
    payload: PublishAutomatedRequest = PublishAutomatedRequest(),
    db: Session = Depends(get_db),
):
    """Sprint 5 — Playwright automation path. Same `human_approved` gate as
    the manual `/publish` above (checked again inside the job itself —
    see app/ai/agents/publish_agent.py's module docstring), plus a check
    that the chosen blog actually has automation credentials configured.
    """
    article = crud.get(db, article_id)
    if not article.human_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot publish: article has not been approved via POST /articles/{id}/approve.",
        )
    if article.status == ArticleStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Article is already published.")

    if payload.blog_platform_id is not None:
        blog_platform = db.get(BlogPlatform, payload.blog_platform_id)
        if blog_platform is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog platform not found")
    else:
        blog_platform = suggest_blog_platform(db)
        if blog_platform is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active blog platform available")

    if not blog_platform.has_automation_credentials:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Blog platform '{blog_platform.name}' has no automation credentials — "
                "set them via POST /blog-platforms/{id}/credentials first."
            ),
        )

    return enqueue_job(
        db,
        job_type=JobType.PUBLISH,
        reference_table="articles",
        reference_id=article.id,
        input_payload={"blog_platform_id": blog_platform.id},
    )
