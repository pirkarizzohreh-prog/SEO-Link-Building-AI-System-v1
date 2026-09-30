"""Endpoint tests for Sprint 5 (Automation): blog platform credentials,
the automated publish trigger, and the status-history endpoint that
docs/API_SPEC.md specified back in Sprint 2 but nothing had implemented
yet.
"""

from __future__ import annotations


def _make_blog_platform(client) -> dict:
    resp = client.post("/api/v1/blog-platforms", json={"name": "Yektablog", "url": "https://yektablog.net"})
    assert resp.status_code == 201
    return resp.json()


def test_set_credentials_admin_only(client, editor_client):
    blog = _make_blog_platform(client)

    forbidden = editor_client.post(
        f"/api/v1/blog-platforms/{blog['id']}/credentials",
        json={"username": "u", "password": "p"},
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"/api/v1/blog-platforms/{blog['id']}/credentials",
        json={"username": "guest-poster", "password": "s3cret", "login_url": "https://yektablog.net/wp-login.php"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["has_automation_credentials"] is True
    assert "password" not in body
    assert "password_encrypted" not in body


def test_blog_platform_starts_without_credentials(client):
    blog = _make_blog_platform(client)
    assert blog["has_automation_credentials"] is False


def _make_topic(client, campaign):
    return client.post(f"/api/v1/campaigns/{campaign['id']}/topics", json={"title": "BOD/COD control"}).json()


def _make_brief(client, topic, target_page):
    return client.post(
        f"/api/v1/topics/{topic['id']}/brief",
        json={
            "target_page_id": target_page["id"],
            "outline": [{"heading": "Intro", "level": "h2", "key_points": ["why it matters"]}],
        },
    ).json()


def _make_approved_article(client, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    brief = _make_brief(client, topic, target_page)
    article = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Managing wastewater",
            "content": "Full article body...",
        },
    ).json()
    approved = client.post(f"/api/v1/articles/{article['id']}/approve").json()
    return approved


def test_publish_automated_requires_credentials(client, campaign, target_page, anchor):
    blog = _make_blog_platform(client)
    article = _make_approved_article(client, campaign, target_page, anchor)

    resp = client.post(
        f"/api/v1/articles/{article['id']}/publish-automated", json={"blog_platform_id": blog["id"]}
    )
    assert resp.status_code == 409
    assert "automation credentials" in resp.json()["detail"]


def test_publish_automated_requires_human_approval(client, campaign, target_page, anchor):
    blog = _make_blog_platform(client)
    client.post(
        f"/api/v1/blog-platforms/{blog['id']}/credentials", json={"username": "u", "password": "p"}
    )
    topic = _make_topic(client, campaign)
    brief = _make_brief(client, topic, target_page)
    article = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Managing wastewater",
            "content": "Full article body...",
        },
    ).json()  # not approved

    resp = client.post(
        f"/api/v1/articles/{article['id']}/publish-automated", json={"blog_platform_id": blog["id"]}
    )
    assert resp.status_code == 409
    assert "not been approved" in resp.json()["detail"]


def test_publish_automated_enqueues_job(client, campaign, target_page, anchor):
    blog = _make_blog_platform(client)
    client.post(
        f"/api/v1/blog-platforms/{blog['id']}/credentials",
        json={"username": "guest-poster", "password": "s3cret"},
    )
    article = _make_approved_article(client, campaign, target_page, anchor)

    resp = client.post(
        f"/api/v1/articles/{article['id']}/publish-automated", json={"blog_platform_id": blog["id"]}
    )
    assert resp.status_code == 202
    job = resp.json()
    assert job["job_type"] == "publish"
    assert job["reference_table"] == "articles"
    assert job["reference_id"] == article["id"]

    # Enqueueing doesn't change the article's status itself — the job does,
    # once (if) it actually succeeds. Unlike /audit, there's no synchronous
    # "in_progress" status for publish in the schema.
    still_approved = client.get(f"/api/v1/articles/{article['id']}").json()
    assert still_approved["status"] == "approved"


def test_publish_automated_defaults_to_suggested_platform(client, campaign, target_page, anchor):
    blog = _make_blog_platform(client)
    client.post(
        f"/api/v1/blog-platforms/{blog['id']}/credentials",
        json={"username": "guest-poster", "password": "s3cret"},
    )
    article = _make_approved_article(client, campaign, target_page, anchor)

    resp = client.post(f"/api/v1/articles/{article['id']}/publish-automated")
    assert resp.status_code == 202


def test_article_status_history(client, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    client.post(f"/api/v1/topics/{topic['id']}/approve")
    brief = _make_brief(client, topic, target_page)
    client.post(f"/api/v1/content-briefs/{brief['id']}/approve")
    article = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Managing wastewater",
            "content": "Full article body...",
        },
    ).json()
    client.post(f"/api/v1/articles/{article['id']}/approve")

    history = client.get(f"/api/v1/articles/{article['id']}/status-history").json()
    assert len(history) == 1
    assert history[0]["stage"] == "human_review"
    assert history[0]["to_status"] == "approved"
