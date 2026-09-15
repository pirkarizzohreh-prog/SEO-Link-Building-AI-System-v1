from tests.conftest import TEST_USER_PASSWORD


def test_login_success(_raw_client, admin_user):
    resp = _raw_client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": TEST_USER_PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_wrong_password(_raw_client, admin_user):
    resp = _raw_client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email(_raw_client):
    resp = _raw_client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(_raw_client):
    assert _raw_client.get("/api/v1/projects").status_code == 401


def test_protected_endpoint_rejects_garbage_token(_raw_client):
    _raw_client.headers["Authorization"] = "Bearer not-a-real-token"
    assert _raw_client.get("/api/v1/projects").status_code == 401


def test_me_returns_current_user(client, admin_user):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == admin_user.email
    assert resp.json()["role"] == "admin"


def test_refresh_issues_new_access_token(_raw_client, admin_user):
    login = _raw_client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": TEST_USER_PASSWORD}
    ).json()

    refresh_resp = _raw_client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refresh_resp.status_code == 200
    new_access = refresh_resp.json()["access_token"]

    _raw_client.headers["Authorization"] = f"Bearer {new_access}"
    assert _raw_client.get("/api/v1/projects").status_code == 200


def test_refresh_token_cannot_be_used_as_access_token(_raw_client, admin_user):
    login = _raw_client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": TEST_USER_PASSWORD}
    ).json()

    _raw_client.headers["Authorization"] = f"Bearer {login['refresh_token']}"
    assert _raw_client.get("/api/v1/projects").status_code == 401


def test_inactive_user_cannot_login_or_use_existing_token(_raw_client, db_session, admin_user):
    from app.core.security import create_access_token

    admin_user.is_active = False
    db_session.commit()

    login_resp = _raw_client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": TEST_USER_PASSWORD}
    )
    assert login_resp.status_code == 401

    _raw_client.headers["Authorization"] = f"Bearer {create_access_token(admin_user.id)}"
    assert _raw_client.get("/api/v1/projects").status_code == 401


def test_only_admin_can_create_users(client, editor_client):
    # `client` is an admin.
    resp = client.post(
        "/api/v1/users", json={"name": "New Editor", "email": "new@example.com", "password": "x" * 12}
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "editor"

    # An editor cannot.
    forbidden = editor_client.post(
        "/api/v1/users", json={"name": "Nope", "email": "nope@example.com", "password": "x" * 12}
    )
    assert forbidden.status_code == 403


def test_cannot_create_duplicate_user_email(client, admin_user):
    resp = client.post(
        "/api/v1/users", json={"name": "Dup", "email": admin_user.email, "password": "x" * 12}
    )
    assert resp.status_code == 409
