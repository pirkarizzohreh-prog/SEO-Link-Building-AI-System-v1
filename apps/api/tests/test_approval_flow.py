"""End-to-end Human Approval Layer / Advanced Content Status Workflow
tests: Idea -> Brief -> Writing -> (Audit skipped, no auditor until
Sprint 4) -> Human Review -> Published. See docs/AI_WORKFLOW.md.
"""

from app.models.approval import Approval
from app.models.content_status_history import ContentStatusHistory


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
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _make_article(client, campaign, target_page, anchor, topic, brief):
    resp = client.post(
        f"/api/v1/campaigns/{campaign['id']}/articles",
        json={
            "target_page_id": target_page["id"],
            "anchor_id": anchor["id"],
            "topic_id": topic["id"],
            "content_brief_id": brief["id"],
            "title": "Challenges of wastewater management",
            "content": "Full article body...",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_topic_approve_writes_approval_and_history(client, db_session, campaign, admin_user):
    topic = _make_topic(client, campaign)

    resp = client.post(f"/api/v1/topics/{topic['id']}/approve", json={"note": "looks good"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "selected"

    approval = db_session.query(Approval).filter(Approval.entity_table == "topics").one()
    assert approval.decision == "approved"
    assert approval.decided_by == admin_user.id
    assert approval.note == "looks good"

    history = db_session.query(ContentStatusHistory).filter(ContentStatusHistory.entity_table == "topics").one()
    assert history.from_status == "suggested"
    assert history.to_status == "selected"
    assert history.actor_type == "user"
    assert history.actor_id == admin_user.id


def test_topic_reject(client, campaign):
    topic = _make_topic(client, campaign)
    resp = client.post(f"/api/v1/topics/{topic['id']}/reject", json={"note": "off-topic"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_brief_approve(client, campaign, target_page):
    topic = _make_topic(client, campaign)
    brief = _make_brief(client, topic, target_page)

    resp = client.post(f"/api/v1/content-briefs/{brief['id']}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_article_cannot_be_published_without_approval(client, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    brief = _make_brief(client, topic, target_page)
    article = _make_article(client, campaign, target_page, anchor, topic, brief)
    blog = client.post(
        "/api/v1/blog-platforms", json={"name": "Yektablog", "url": "https://yektablog.net"}
    ).json()

    assert article["human_approved"] is False

    publish_resp = client.post(
        f"/api/v1/articles/{article['id']}/publish",
        json={"blog_platform_id": blog["id"], "published_url": "https://yektablog.net/post/1"},
    )
    assert publish_resp.status_code == 409

    package_resp = client.get(f"/api/v1/articles/{article['id']}/publish-package")
    assert package_resp.status_code == 409


def test_full_approval_to_publish_flow(client, db_session, campaign, target_page, anchor, admin_user):
    topic = _make_topic(client, campaign)
    client.post(f"/api/v1/topics/{topic['id']}/approve")

    brief = _make_brief(client, topic, target_page)
    client.post(f"/api/v1/content-briefs/{brief['id']}/approve")

    article = _make_article(client, campaign, target_page, anchor, topic, brief)
    blog = client.post(
        "/api/v1/blog-platforms", json={"name": "Yektablog", "url": "https://yektablog.net"}
    ).json()

    approve_resp = client.post(f"/api/v1/articles/{article['id']}/approve", json={"note": "ready"})
    assert approve_resp.status_code == 200
    approved = approve_resp.json()
    assert approved["human_approved"] is True
    assert approved["human_approved_by"] == admin_user.id
    assert approved["human_approved_at"] is not None
    assert approved["status"] == "approved"

    package = client.get(f"/api/v1/articles/{article['id']}/publish-package")
    assert package.status_code == 200
    assert package.json()["anchor_text"] == anchor["anchor_text"]
    assert package.json()["target_url"] == target_page["url"]
    assert package.json()["suggested_blog_platform_id"] == blog["id"]

    publish_resp = client.post(
        f"/api/v1/articles/{article['id']}/publish",
        json={"blog_platform_id": blog["id"], "published_url": "https://yektablog.net/post/1"},
    )
    assert publish_resp.status_code == 200
    published = publish_resp.json()
    assert published["status"] == "published"
    assert published["published_url"] == "https://yektablog.net/post/1"

    # Publishing twice is refused.
    assert (
        client.post(
            f"/api/v1/articles/{article['id']}/publish",
            json={"blog_platform_id": blog["id"], "published_url": "https://yektablog.net/post/1"},
        ).status_code
        == 409
    )

    publications = client.get(f"/api/v1/articles/{article['id']}/publications").json()
    assert len(publications) == 1
    assert publications[0]["method"] == "manual"

    pre_publish_approval = (
        db_session.query(Approval)
        .filter(Approval.entity_table == "articles", Approval.approval_type == "pre_publish")
        .one()
    )
    assert pre_publish_approval.decided_by == admin_user.id


def test_article_reject(client, campaign, target_page, anchor):
    topic = _make_topic(client, campaign)
    brief = _make_brief(client, topic, target_page)
    article = _make_article(client, campaign, target_page, anchor, topic, brief)

    resp = client.post(f"/api/v1/articles/{article['id']}/reject", json={"note": "off-brand"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["human_approved"] is False


def test_editor_can_also_approve_articles(editor_client, db_session, editor_user):
    # An editor (not just admin) is allowed to drive the approval workflow —
    # per docs/DATABASE_SCHEMA.md: "editor: فقط CRUD محتوا و تأیید".
    project = editor_client.post(
        "/api/v1/projects", json={"project_name": "P", "website_url": "https://example.com"}
    ).json()
    target_page = editor_client.post(
        f"/api/v1/projects/{project['id']}/target-pages",
        json={"title": "T", "url": "https://example.com/t", "main_keyword": "kw"},
    ).json()
    campaign = editor_client.post(
        "/api/v1/campaigns",
        json={
            "project_id": project["id"],
            "target_page_id": target_page["id"],
            "name": "C",
            "total_links_target": 5,
            "blog_count": 2,
            "duration_days": 30,
        },
    ).json()
    topic = _make_topic(editor_client, campaign)

    resp = editor_client.post(f"/api/v1/topics/{topic['id']}/approve")
    assert resp.status_code == 200

    approval = db_session.query(Approval).filter(Approval.entity_table == "topics").one()
    assert approval.decided_by == editor_user.id
