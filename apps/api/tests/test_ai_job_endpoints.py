"""Tests the enqueue-only endpoints added in Sprint 3 — they must return
fast (no LLM call in the request path) and enforce the same preconditions
documented in docs/API_SPEC.md (e.g. a topic must be approved before a
brief can be generated for it).
"""

from __future__ import annotations


def test_start_campaign_enqueues_keyword_intel_job(client, campaign):
    resp = client.post(f"/api/v1/campaigns/{campaign['id']}/start")
    assert resp.status_code == 202
    job = resp.json()
    assert job["job_type"] == "keyword_intel"
    assert job["status"] == "pending"

    updated_campaign = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert updated_campaign["status"] == "in_progress"


def test_start_campaign_twice_conflicts(client, campaign):
    client.post(f"/api/v1/campaigns/{campaign['id']}/start")
    resp = client.post(f"/api/v1/campaigns/{campaign['id']}/start")
    assert resp.status_code == 409


def test_pause_campaign(client, campaign):
    client.post(f"/api/v1/campaigns/{campaign['id']}/start")
    resp = client.post(f"/api/v1/campaigns/{campaign['id']}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"

    # Paused campaigns can be started again.
    assert client.post(f"/api/v1/campaigns/{campaign['id']}/start").status_code == 202


def test_generate_brief_requires_approved_topic(client, campaign):
    topic = client.post(f"/api/v1/campaigns/{campaign['id']}/topics", json={"title": "T"}).json()

    conflict = client.post(f"/api/v1/topics/{topic['id']}/generate-brief")
    assert conflict.status_code == 409

    client.post(f"/api/v1/topics/{topic['id']}/approve")
    resp = client.post(f"/api/v1/topics/{topic['id']}/generate-brief")
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "brief_generation"


def test_generate_article_requires_approved_brief(client, campaign, target_page):
    topic = client.post(f"/api/v1/campaigns/{campaign['id']}/topics", json={"title": "T"}).json()
    client.post(f"/api/v1/topics/{topic['id']}/approve")
    brief = client.post(
        f"/api/v1/topics/{topic['id']}/brief",
        json={"target_page_id": target_page["id"], "outline": [{"heading": "H", "level": "h2", "key_points": []}]},
    ).json()

    conflict = client.post(f"/api/v1/content-briefs/{brief['id']}/generate-article")
    assert conflict.status_code == 409

    client.post(f"/api/v1/content-briefs/{brief['id']}/approve")
    resp = client.post(f"/api/v1/content-briefs/{brief['id']}/generate-article")
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "article_write"


def test_analyze_competitor_page_requires_linked_target_page(client, project):
    competitor = client.post(
        f"/api/v1/projects/{project['id']}/competitors",
        json={"name": "Competitor A", "website_url": "https://competitor-a.example.com"},
    ).json()
    page = client.post(
        f"/api/v1/competitors/{competitor['id']}/pages", json={"url": "https://competitor-a.example.com/blog"}
    ).json()

    conflict = client.post(f"/api/v1/competitor-pages/{page['id']}/analyze")
    assert conflict.status_code == 409


def test_analyze_competitor_page_enqueues_job(client, project, target_page):
    competitor = client.post(
        f"/api/v1/projects/{project['id']}/competitors",
        json={"name": "Competitor A", "website_url": "https://competitor-a.example.com"},
    ).json()
    page = client.post(
        f"/api/v1/competitors/{competitor['id']}/pages",
        json={"url": "https://competitor-a.example.com/blog", "target_page_id": target_page["id"]},
    ).json()

    resp = client.post(f"/api/v1/competitor-pages/{page['id']}/analyze")
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "competitor_analysis"

    listed = client.get(f"/api/v1/competitors/{competitor['id']}/pages").json()
    assert len(listed) == 1
    assert listed[0]["id"] == page["id"]


def test_analyze_internal_links_enqueues_job(client, project):
    resp = client.post(f"/api/v1/projects/{project['id']}/analyze-internal-links")
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "internal_link_suggestion"


def test_analyze_internal_links_404_for_missing_project(client):
    assert client.post("/api/v1/projects/999999/analyze-internal-links").status_code == 404


def test_jobs_are_listable_after_enqueue(client, campaign):
    client.post(f"/api/v1/campaigns/{campaign['id']}/start")
    jobs = client.get("/api/v1/jobs?job_type=keyword_intel").json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "pending"

    detail = client.get(f"/api/v1/jobs/{jobs[0]['id']}")
    assert detail.status_code == 200
