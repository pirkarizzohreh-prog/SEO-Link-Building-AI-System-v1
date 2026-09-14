from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
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


# NOTE: POST /campaigns/{id}/start (kicks off the AI pipeline) and
# POST /campaigns/{id}/pause are added in Sprint 3 (AI Agents), once the
# job worker exists to actually act on the ai_jobs rows it would create.
