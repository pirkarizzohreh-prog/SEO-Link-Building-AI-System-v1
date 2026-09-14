from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article, ArticleStatus
from app.models.publication import Publication
from app.models.seo_audit_result import SeoAuditResult
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate, PublicationRead, SeoAuditResultRead
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


# NOTE: POST /articles/{id}/audit is an AI job — Sprint 4 (SEO Audit).
# POST /articles/{id}/approve, /reject and /publish all require the
# Human Approval Layer (an authenticated `decided_by` user) — Sprint 2 —
# and /publish's automated path is Sprint 5. `human_approved` is never
# settable through ArticleUpdate; see app/models/article.py.
