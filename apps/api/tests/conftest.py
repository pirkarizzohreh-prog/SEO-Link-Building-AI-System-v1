from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers every table on Base.metadata
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.campaign import Campaign
from app.models.project import Project
from app.models.target_page import TargetPage
from app.models.user import User, UserRole

# In-memory SQLite, shared across connections in the same test via
# StaticPool — fast, and isolated per test function (see `db_session`).
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_USER_PASSWORD = "correcthorsebatterystaple"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def _db_override(db_session: Session) -> Generator[None, None, None]:
    """Wires FastAPI's `get_db` dependency to this test's session. Each of
    the client fixtures below gets its *own* TestClient instance (each
    with independent `.headers`) but they all share this same override —
    sharing a single TestClient across fixtures instead would mean the
    last one to set `Authorization` wins for all of them.
    """
    def _get_db_override() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _get_db_override
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def _raw_client(_db_override: None) -> Generator[TestClient, None, None]:
    """An unauthenticated TestClient — no default Authorization header.
    Use this directly only for auth-flow tests (login, 401 checks); every
    other test should use `client` or `editor_client` below.
    """
    with TestClient(fastapi_app) as test_client:
        yield test_client


def _make_user(db_session: Session, *, role: UserRole, email: str) -> User:
    user = User(name=role.value.title(), email=email, password_hash=hash_password(TEST_USER_PASSWORD), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    return _make_user(db_session, role=UserRole.ADMIN, email="admin@example.com")


@pytest.fixture()
def editor_user(db_session: Session) -> User:
    return _make_user(db_session, role=UserRole.EDITOR, email="editor@example.com")


@pytest.fixture()
def client(_db_override: None, admin_user: User) -> Generator[TestClient, None, None]:
    """The default, pre-authenticated (as an admin) client used by most
    tests — Sprint 1's CRUD tests all assume this. Sprint 2's own
    auth/role tests use `_raw_client` or `editor_client` instead. This is
    a *separate* TestClient instance from `_raw_client`/`editor_client`
    (see `_db_override`), so using more than one in the same test doesn't
    clobber a shared `Authorization` header.
    """
    with TestClient(fastapi_app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {create_access_token(admin_user.id)}"
        yield test_client


@pytest.fixture()
def editor_client(_db_override: None, editor_user: User) -> Generator[TestClient, None, None]:
    with TestClient(fastapi_app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {create_access_token(editor_user.id)}"
        yield test_client


# --- Shared pipeline fixtures (project -> target_page -> anchor -> campaign) ---
# Used by both test_pipeline_crud.py and test_approval_flow.py.


@pytest.fixture()
def project(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/projects", json={"project_name": "AEB Water", "website_url": "https://aebwater.com"}
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def target_page(client: TestClient, project: dict) -> dict:
    resp = client.post(
        f"/api/v1/projects/{project['id']}/target-pages",
        json={
            "title": "Food industry wastewater package",
            "url": "https://aebwater.com/product/food-wastewater-package/",
            "main_keyword": "food industry wastewater package",
            "page_type": "product",
            "priority": 1,
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def anchor(client: TestClient, target_page: dict) -> dict:
    resp = client.post(
        f"/api/v1/target-pages/{target_page['id']}/anchors",
        json={"anchor_text": "food industry wastewater package", "anchor_type": "exact"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def campaign(client: TestClient, project: dict, target_page: dict) -> dict:
    resp = client.post(
        "/api/v1/campaigns",
        json={
            "project_id": project["id"],
            "target_page_id": target_page["id"],
            "name": "AEB - Dairy Industry Links",
            "total_links_target": 20,
            "blog_count": 10,
            "duration_days": 60,
        },
    )
    assert resp.status_code == 201
    return resp.json()


# --- Same pipeline, built directly against the DB session (no HTTP round
# trip, no auth) — for tests exercising agents/handlers/worker directly
# rather than the API layer. `db_` prefix distinguishes these ORM-object
# fixtures from the dict-returning, client-based ones above.


@pytest.fixture()
def db_project(db_session: Session) -> Project:
    project = Project(project_name="AEB Water", website_url="https://aebwater.com")
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture()
def db_target_page(db_session: Session, db_project: Project) -> TargetPage:
    tp = TargetPage(
        project_id=db_project.id,
        title="Food industry wastewater package",
        url="https://aebwater.com/product/food-wastewater-package/",
        main_keyword="food industry wastewater package",
    )
    db_session.add(tp)
    db_session.commit()
    return tp


@pytest.fixture()
def db_campaign(db_session: Session, db_project: Project, db_target_page: TargetPage) -> Campaign:
    campaign = Campaign(
        project_id=db_project.id,
        target_page_id=db_target_page.id,
        name="AEB - Dairy Industry Links",
        total_links_target=20,
        blog_count=10,
        duration_days=60,
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign
