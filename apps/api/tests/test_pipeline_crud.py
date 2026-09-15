# `project`, `target_page`, `anchor` and `campaign` fixtures now live in
# conftest.py (shared with tests/test_approval_flow.py).


def test_target_page_and_keyword_crud(client, target_page):
    kw_resp = client.post(
        f"/api/v1/target-pages/{target_page['id']}/keywords",
        json={"keyword": "industrial wastewater treatment", "type": "related"},
    )
    assert kw_resp.status_code == 201

    list_resp = client.get(f"/api/v1/target-pages/{target_page['id']}/keywords")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_anchor_distribution_reflects_usage(client, target_page, anchor):
    dist = client.get(f"/api/v1/target-pages/{target_page['id']}/anchors/distribution")
    assert dist.status_code == 200
    body = dist.json()
    # No usage yet -> the default global target ratio, zero actuals.
    assert body["target_ratio"] == {"exact": 30, "partial": 35, "semantic": 20, "brand": 15}
    assert body["actual_counts"] == {"exact": 0, "partial": 0, "semantic": 0, "brand": 0}


def test_campaign_and_topic_lifecycle(client, campaign):
    topic_resp = client.post(
        f"/api/v1/campaigns/{campaign['id']}/topics",
        json={"title": "Challenges of wastewater management in food factories"},
    )
    assert topic_resp.status_code == 201
    topic = topic_resp.json()
    assert topic["status"] == "suggested"
    assert topic["generated_by"] == "manual"

    update_resp = client.put(f"/api/v1/topics/{topic['id']}", json={"status": "selected"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "selected"

    list_resp = client.get(f"/api/v1/campaigns/{campaign['id']}/topics")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_content_brief_and_article_chain(client, campaign, target_page, anchor):
    topic = client.post(
        f"/api/v1/campaigns/{campaign['id']}/topics", json={"title": "BOD/COD control in food plants"}
    ).json()

    brief_resp = client.post(
        f"/api/v1/topics/{topic['id']}/brief",
        json={
            "target_page_id": target_page["id"],
            "outline": [{"heading": "Intro", "level": "h2", "key_points": ["why it matters"]}],
            "target_word_count": 1200,
        },
    )
    assert brief_resp.status_code == 201
    brief = brief_resp.json()

    article_resp = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Challenges of wastewater management in food factories",
            "content": "Full article body here...",
        },
    )
    assert article_resp.status_code == 201
    article = article_resp.json()
    assert article["status"] == "draft"
    assert article["human_approved"] is False

    # human_approved is not part of ArticleUpdate — it must stay untouched
    # even if a client tries to sneak it into the payload (extra fields are
    # ignored by pydantic unless configured otherwise, so this documents
    # the current behaviour rather than a security boundary by itself; the
    # real enforcement is that ArticleUpdate has no such field at all).
    patched = client.put(
        f"/api/v1/articles/{article['id']}", json={"title": "Updated title", "human_approved": True}
    )
    assert patched.status_code == 200
    assert patched.json()["human_approved"] is False
    assert patched.json()["title"] == "Updated title"


def test_link_placement_rule_resolution_hierarchy(client, project, campaign):
    # No rules at all yet -> falls back to schema defaults.
    resolved = client.get(f"/api/v1/link-placement-rules/resolve?campaign_id={campaign['id']}").json()
    assert resolved["resolved_from"] == "global"
    assert resolved["anchor_distribution"] == {"exact": 30, "partial": 35, "semantic": 20, "brand": 15}

    # A project-level override should now win over the (still-absent) global row.
    client.post(
        "/api/v1/link-placement-rules",
        json={
            "scope": "project",
            "scope_id": project["id"],
            "anchor_distribution": {"exact": 25, "partial": 40, "semantic": 20, "brand": 15},
        },
    )
    resolved = client.get(f"/api/v1/link-placement-rules/resolve?campaign_id={campaign['id']}").json()
    assert resolved["resolved_from"] == "project"
    assert resolved["anchor_distribution"]["exact"] == 25

    # A campaign-level override should win over the project one.
    client.post(
        "/api/v1/link-placement-rules",
        json={
            "scope": "campaign",
            "scope_id": campaign["id"],
            "anchor_distribution": {"exact": 10, "partial": 40, "semantic": 30, "brand": 20},
        },
    )
    resolved = client.get(f"/api/v1/link-placement-rules/resolve?campaign_id={campaign['id']}").json()
    assert resolved["resolved_from"] == "campaign"
    assert resolved["anchor_distribution"]["exact"] == 10


def test_competitor_intelligence_crud(client, project, target_page):
    competitor = client.post(
        f"/api/v1/projects/{project['id']}/competitors",
        json={"name": "Competitor A", "website_url": "https://competitor-a.example.com"},
    ).json()

    page = client.post(
        f"/api/v1/competitors/{competitor['id']}/pages",
        json={"url": "https://competitor-a.example.com/blog/wastewater", "target_page_id": target_page["id"]},
    )
    assert page.status_code == 201

    # No gaps recorded manually here (that's the AI job's job, Sprint 3) —
    # just check the listing endpoint works end to end.
    gaps = client.get(f"/api/v1/target-pages/{target_page['id']}/content-gaps")
    assert gaps.status_code == 200
    assert gaps.json() == []


def test_serp_snapshot_crud(client, target_page):
    resp = client.post(
        f"/api/v1/target-pages/{target_page['id']}/serp-snapshots",
        json={
            "keyword": "food industry wastewater package",
            "results": [{"position": 1, "url": "https://a.example.com", "title": "A", "snippet": "...", "domain": "a.example.com"}],
            "fetched_at": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["source"] == "manual"


def test_content_and_prompt_templates(client):
    template = client.post(
        "/api/v1/content-templates",
        json={"name": "Educational How-To", "default_word_count": 1200},
    )
    assert template.status_code == 201

    prompt_v1 = client.post(
        "/api/v1/prompt-templates",
        json={"agent_type": "article_write", "name": "Writer v1", "template_text": "Write an article about {{topic}}"},
    )
    assert prompt_v1.status_code == 201
    assert prompt_v1.json()["version"] == 1
    assert prompt_v1.json()["is_active"] is True

    prompt_v2 = client.post(
        "/api/v1/prompt-templates",
        json={"agent_type": "article_write", "name": "Writer v2", "template_text": "Write a better article about {{topic}}"},
    )
    assert prompt_v2.status_code == 201
    assert prompt_v2.json()["version"] == 2

    active = client.get("/api/v1/prompt-templates/article_write/active")
    assert active.status_code == 200
    assert active.json()["version"] == 2

    all_versions = client.get("/api/v1/prompt-templates?agent_type=article_write")
    assert len(all_versions.json()) == 2


def test_internal_link_suggestions_status_updates(client, db_session, project, target_page):
    # Create a second target page to link to/from.
    target_page_2 = client.post(
        f"/api/v1/projects/{project['id']}/target-pages",
        json={
            "title": "Pharma wastewater treatment",
            "url": "https://aebwater.com/article/pharma-wastewater/",
            "main_keyword": "pharmaceutical industry wastewater treatment",
        },
    ).json()

    # Sprint 1 exposes no create endpoint for suggestions (they come from
    # the Internal Link Suggestion Agent in Sprint 3), so insert one
    # directly to exercise the apply/dismiss status-update endpoints.
    from app.models.internal_link_suggestion import InternalLinkSuggestion

    suggestion = InternalLinkSuggestion(
        project_id=project["id"],
        source_target_page_id=target_page["id"],
        destination_target_page_id=target_page_2["id"],
        suggested_anchor="pharmaceutical wastewater treatment",
    )
    db_session.add(suggestion)
    db_session.commit()
    db_session.refresh(suggestion)

    listing = client.get(f"/api/v1/projects/{project['id']}/internal-link-suggestions")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["status"] == "suggested"

    applied = client.post(f"/api/v1/internal-link-suggestions/{suggestion.id}/apply")
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"


def test_jobs_endpoint_is_read_only_and_empty(client):
    resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200
    assert resp.json() == []
