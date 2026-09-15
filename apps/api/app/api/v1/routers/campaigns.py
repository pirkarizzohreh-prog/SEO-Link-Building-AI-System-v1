from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_job import JobType
from app.models.campaign import Campaign, CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.job import AiJobRead
from app.services.job_service import enqueue_job
from app.utils.crud import CRUDBase

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
crud = CRUDBase(Campaign)


@router.get("", response_model=list[CampaignRead])
def list_campaigns(
    project_id: int | None = None,
    status: CampaignStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.list(db, skip=skip, limit=limit, project_id=project_id, status=status)


@router.post("", response_model=CampaignRead, status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    return crud.create(db, payload)


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    return crud.get(db, campaign_id)


@router.put("/{campaign_id}", response_model=CampaignRead)
def update_campaign(campaign_id: int, payload: CampaignUpdate, db: Session = Depends(get_db)):
    return crud.update(db, campaign_id, payload)


@router.post("/{campaign_id}/start", response_model=AiJobRead, status_code=202)
def start_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Kicks off Stage: Idea — a keyword_intel job, which the worker
    automatically chains into topic_gen on success (see
    app/jobs/handlers.py and docs/AI_WORKFLOW.md).
    """
    campaign = crud.get(db, campaign_id)
    if campaign.status not in (CampaignStatus.PLANNING, CampaignStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign {campaign_id} is already {campaign.status.value}",
        )
    job = enqueue_job(db, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=campaign.id)
    campaign.status = CampaignStatus.IN_PROGRESS
    db.commit()
    return job


@router.post("/{campaign_id}/pause", response_model=CampaignRead)
def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = crud.get(db, campaign_id)
    campaign.status = CampaignStatus.PAUSED
    db.commit()
    db.refresh(campaign)
    return campaign
