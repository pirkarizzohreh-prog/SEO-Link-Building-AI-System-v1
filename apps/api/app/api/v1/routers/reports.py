"""Report Manager — docs/AI_WORKFLOW.md ("مرحله ۱۰"), docs/API_SPEC.md
("Reports"). Read-only, no AI involved — see app/services/report_service.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.project import Project
from app.schemas.report import CampaignReport, PipelineStats, ProjectReport
from app.services.report_service import build_campaign_report, build_pipeline_stats, build_project_report
from app.utils.crud import CRUDBase

router = APIRouter(tags=["Reports"])
_project_crud = CRUDBase(Project)
_campaign_crud = CRUDBase(Campaign)


@router.get("/projects/{project_id}/report", response_model=ProjectReport)
def get_project_report(project_id: int, db: Session = Depends(get_db)):
    project = _project_crud.get(db, project_id)
    return build_project_report(db, project)


@router.get("/campaigns/{campaign_id}/report", response_model=CampaignReport)
def get_campaign_report(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_crud.get(db, campaign_id)
    return build_campaign_report(db, campaign)


@router.get("/campaigns/{campaign_id}/pipeline-stats", response_model=PipelineStats)
def get_pipeline_stats(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_crud.get(db, campaign_id)
    return build_pipeline_stats(db, campaign)
