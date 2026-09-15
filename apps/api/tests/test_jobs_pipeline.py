"""Tests app.jobs.handlers.process_job and app.jobs.worker.claim_next_job:
job lifecycle (pending -> running -> success/failed) and the automatic
keyword_intel -> topic_gen chain — see docs/AI_WORKFLOW.md.
"""

from __future__ import annotations

import json

from app.jobs.handlers import process_job
from app.jobs.worker import claim_next_job
from app.models.ai_job import AiJob, JobStatus, JobType
from app.models.keyword import Keyword
from app.models.topic import Topic
from app.services.job_service import enqueue_job
from tests.fake_llm_client import FakeLLMClient


def test_process_job_success_updates_job_row(db_session, db_campaign):
    job = enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)
    client = FakeLLMClient([json.dumps({"related_keywords": [{"keyword": "wastewater", "type": "related"}]})])

    process_job(db_session, job, client)

    db_session.refresh(job)
    assert job.status == JobStatus.SUCCESS
    assert job.tokens_used == 100
    assert job.output_payload["created_keywords"] == ["wastewater"]
    assert job.started_at is not None and job.finished_at is not None
    assert job.provider == client.provider_name


def test_process_job_chains_keyword_intel_into_topic_gen(db_session, db_campaign):
    job = enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)
    client = FakeLLMClient([json.dumps({"related_keywords": []})])

    process_job(db_session, job, client)

    chained = db_session.query(AiJob).filter(AiJob.job_type == JobType.TOPIC_GEN).all()
    assert len(chained) == 1
    assert chained[0].status == JobStatus.PENDING
    assert chained[0].reference_table == "campaigns"
    assert chained[0].reference_id == db_campaign.id


def test_process_job_failure_marks_job_failed_and_rolls_back_partial_writes(db_session, db_campaign):
    job = enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)
    # Not valid JSON -> the agent raises inside parse_json_response.
    client = FakeLLMClient(["not json at all"])

    process_job(db_session, job, client)

    db_session.refresh(job)
    assert job.status == JobStatus.FAILED
    assert "valid JSON" in job.error_message
    assert db_session.query(Keyword).filter(Keyword.target_page_id == db_campaign.target_page_id).count() == 0
    # No chained topic_gen job on failure.
    assert db_session.query(AiJob).filter(AiJob.job_type == JobType.TOPIC_GEN).count() == 0


def test_full_pipeline_keyword_intel_to_topics(db_session, db_campaign):
    job = enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)
    process_job(db_session, job, FakeLLMClient([json.dumps({"related_keywords": [{"keyword": "kw1", "type": "related"}]})]))

    next_job = claim_next_job(db_session)
    assert next_job is not None
    assert next_job.job_type == JobType.TOPIC_GEN

    process_job(
        db_session,
        next_job,
        FakeLLMClient([json.dumps({"topics": [{"title": "Topic A", "rationale": "r"}, {"title": "Topic B", "rationale": "r"}]})]),
    )

    topics = db_session.query(Topic).filter(Topic.campaign_id == db_campaign.id).all()
    assert {t.title for t in topics} == {"Topic A", "Topic B"}

    # Nothing left pending — the chain stops at topic_gen (human approval
    # gates the next step, per docs/AI_WORKFLOW.md).
    assert claim_next_job(db_session) is None


def test_claim_next_job_returns_oldest_pending(db_session, db_campaign):
    older = enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)
    enqueue_job(db_session, job_type=JobType.KEYWORD_INTEL, reference_table="campaigns", reference_id=db_campaign.id)

    claimed = claim_next_job(db_session)
    assert claimed.id == older.id


def test_unregistered_job_type_fails_cleanly(db_session, db_campaign):
    # SERP_FETCH exists in the enum (for a future SerpAPI integration —
    # see docs/DATABASE_SCHEMA.md) but has no agent yet.
    job = enqueue_job(db_session, job_type=JobType.SERP_FETCH, reference_table="campaigns", reference_id=db_campaign.id)
    process_job(db_session, job, FakeLLMClient([]))
    db_session.refresh(job)
    assert job.status == JobStatus.FAILED
    assert "No agent registered" in job.error_message
