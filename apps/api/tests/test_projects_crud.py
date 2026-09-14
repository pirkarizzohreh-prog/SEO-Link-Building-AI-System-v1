def test_project_crud_lifecycle(client):
    create_resp = client.post(
        "/api/v1/projects",
        json={
            "project_name": "AEB Water",
            "website_url": "https://aebwater.com",
            "industry": "Water & Wastewater Treatment",
        },
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["status"] == "active"
    project_id = project["id"]

    get_resp = client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["project_name"] == "AEB Water"

    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.put(f"/api/v1/projects/{project_id}", json={"status": "inactive"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "inactive"

    delete_resp = client.delete(f"/api/v1/projects/{project_id}")
    assert delete_resp.status_code == 204

    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_project_not_found(client):
    assert client.get("/api/v1/projects/999").status_code == 404


def test_project_knowledge_base_upsert(client):
    project = client.post(
        "/api/v1/projects", json={"project_name": "AEB Water", "website_url": "https://aebwater.com"}
    ).json()

    # Not set yet.
    assert client.get(f"/api/v1/projects/{project['id']}/knowledge-base").status_code == 404

    put_resp = client.put(
        f"/api/v1/projects/{project['id']}/knowledge-base",
        json={"brand_name": "AEB Water", "brand_voice_tone": "technical, data-driven"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["brand_name"] == "AEB Water"

    # Upsert again should update, not duplicate.
    put_resp_2 = client.put(
        f"/api/v1/projects/{project['id']}/knowledge-base",
        json={"brand_name": "AEB Water Updated"},
    )
    assert put_resp_2.status_code == 200
    assert put_resp_2.json()["brand_name"] == "AEB Water Updated"
    assert put_resp_2.json()["id"] == put_resp.json()["id"]
