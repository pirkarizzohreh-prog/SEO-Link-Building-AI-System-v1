"""Report Manager tests — docs/AI_WORKFLOW.md ("مرحله ۱۰ — Report
Manager"), docs/API_SPEC.md ("Reports"). Drives a project through the full
pipeline (Idea -> Brief -> Writing -> Audit -> Human Review -> Published)
via the real endpoints + the real SEO Auditor job, then checks the report
numbers against what actually happened.
"""

from __future__ import annotations

import json

from app.jobs.handlers import process_job
from app.jobs.worker import claim_next_job
from tests.fake_llm_client import FakeLLMClient

GOOD_TONE_JSON = json.dumps({"tone_score": 90, "forbidden_words_found": [], "reason": "لحن مناسب است"})


def _make_topic(client, campaign):
    resp = client.post(f"/api/v1/campaigns/{campaign['id']}/topics", json={"title": "BOD/COD control"})
    assert resp.status_code == 201
    return resp.json()


def _make_brief(client, topic, target_page):
    resp = client.post(
        f"/api/v1/topics/{topic['id']}/brief",
        json={
            "target_page_id": target_page["id"],
            "outline": [{"heading": "Intro", "level": "h2", "key_points": ["why it matters"]}],
            "target_word_count": 5,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _make_article(client, campaign, target_page, anchor, topic, brief, content):
    resp = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Wastewater management",
            "content": content,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _write_article_via_agent(client, db_session, brief: dict, anchor: dict, target_page: dict) -> dict:
    """Goes through the real Article Writer job (not manual creation) so
    `anchor_usage_log` actually gets a row — needed to exercise the
    campaign report's anchor distribution numbers. The only active anchor
    on `target_page` is the fixture's exact-match one, so the writer is
    guaranteed to pick it; the canned response includes that exact anchor
    text + URL so the SEO Auditor's hard checks pass on the first try.
    """
    assert client.post(f"/api/v1/content-briefs/{brief['id']}/generate-article").status_code == 202
    job = claim_next_job(db_session)
    process_job(db_session, job, FakeLLMClient([_passing_content(anchor, target_page)]))
    db_session.commit()
    article_id = job.output_payload["article_id"]
    return client.get(f"/api/v1/articles/{article_id}").json()


def _passing_content(anchor: dict, target_page: dict) -> str:
    filler = "این یک مقاله خوب و طولانی درباره تصفیه فاضلاب صنایع غذایی است. " * 5
    return f"## Intro\n[{anchor['anchor_text']}]({target_page['url']}) {filler}"


def _run_audit_to_completion(client, db_session, article: dict) -> None:
    assert client.post(f"/api/v1/articles/{article['id']}/audit").status_code == 202
    job = claim_next_job(db_session)
    process_job(db_session, job, FakeLLMClient([GOOD_TONE_JSON]))
    db_session.commit()


def test_project_and_campaign_report_after_publish(client, db_session, project, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    client.post(f"/api/v1/topics/{topic['id']}/approve")
    brief = _make_brief(client, topic, target_page)
    client.post(f"/api/v1/content-briefs/{brief['id']}/approve")

    article = _write_article_via_agent(client, db_session, brief, anchor, target_page)
    _run_audit_to_completion(client, db_session, article)

    audited = client.get(f"/api/v1/articles/{article['id']}").json()
    assert audited["status"] == "reviewed"

    client.post(f"/api/v1/articles/{article['id']}/approve")
    blog = client.post(
        "/api/v1/blog-platforms", json={"name": "Yektablog", "url": "https://yektablog.net"}
    ).json()
    client.post(
        f"/api/v1/articles/{article['id']}/publish",
        json={"blog_platform_id": blog["id"], "published_url": "https://yektablog.net/post/1"},
    )

    project_report = client.get(f"/api/v1/projects/{project['id']}/report").json()
    assert project_report["total_links_built"] == 1
    assert project_report["pages_covered"] == 1
    assert project_report["total_campaigns"] == 1

    campaign_report = client.get(f"/api/v1/campaigns/{campaign['id']}/report").json()
    assert campaign_report["published_urls"] == ["https://yektablog.net/post/1"]
    assert campaign_report["total_articles"] == 1
    assert campaign_report["audited_articles"] == 1
    assert campaign_report["audit_success_rate"] == 100.0
    assert sum(campaign_report["anchor_distribution_actual"].values()) == 1
    assert campaign_report["anchor_distribution_target"] == {"exact": 30, "partial": 35, "semantic": 20, "brand": 15}


def test_pipeline_stats_reports_stage_durations(client, db_session, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    client.post(f"/api/v1/topics/{topic['id']}/approve")
    brief = _make_brief(client, topic, target_page)
    client.post(f"/api/v1/content-briefs/{brief['id']}/approve")

    article = _make_article(client, campaign, target_page, anchor, topic, brief, _passing_content(anchor, target_page))
    _run_audit_to_completion(client, db_session, article)

    stats = client.get(f"/api/v1/campaigns/{campaign['id']}/pipeline-stats").json()
    assert stats["campaign_id"] == campaign["id"]
    for stage in ("idea", "brief", "audit"):
        assert stage in stats["stages"]
        assert stats["stages"][stage]["sample_count"] == 1
        assert stats["stages"][stage]["avg_hours"] >= 0


def test_project_report_with_no_activity(client, project):
    report = client.get(f"/api/v1/projects/{project['id']}/report").json()
    assert report == {
        "project_id": project["id"],
        "project_name": project["project_name"],
        "total_target_pages": 0,
        "total_campaigns": 0,
        "total_links_built": 0,
        "pages_covered": 0,
    }


def test_campaign_report_with_no_articles_has_no_audit_rate(client, campaign):
    report = client.get(f"/api/v1/campaigns/{campaign['id']}/report").json()
    assert report["audit_success_rate"] is None
    assert report["total_articles"] == 0
    assert report["published_urls"] == []


def test_reports_404_for_unknown_ids(client):
    assert client.get("/api/v1/projects/999999/report").status_code == 404
    assert client.get("/api/v1/campaigns/999999/report").status_code == 404
    assert client.get("/api/v1/campaigns/999999/pipeline-stats").status_code == 404
