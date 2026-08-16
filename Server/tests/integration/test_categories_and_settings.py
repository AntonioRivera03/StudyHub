from tests.conftest import ApiContext


def test_category_soft_delete_and_restore(api_context: ApiContext) -> None:
    client = api_context.client
    created_response = client.post(
        "/api/v1/categories", json={"name": "Mathematics", "color": "#3366ff"}
    )
    assert created_response.status_code == 201
    category_id = created_response.json()["id"]

    updated_response = client.patch(
        f"/api/v1/categories/{category_id}", json={"name": "Advanced mathematics"}
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["name"] == "Advanced mathematics"

    assert client.delete(f"/api/v1/categories/{category_id}").status_code == 204
    assert client.get(f"/api/v1/categories/{category_id}").status_code == 404
    assert client.get("/api/v1/categories").json() == []
    deleted = client.get("/api/v1/categories?include_deleted=true").json()
    assert deleted[0]["deleted_at"] is not None

    restored_response = client.post(f"/api/v1/categories/{category_id}/restore")
    assert restored_response.status_code == 200
    assert restored_response.json()["deleted_at"] is None
    assert len(client.get("/api/v1/categories").json()) == 1


def test_pomodoro_settings_defaults_update_and_validation(api_context: ApiContext) -> None:
    client = api_context.client
    response = client.get("/api/v1/settings/pomodoro")
    assert response.status_code == 200
    assert response.json()["focus_minutes"] == 25
    assert response.json()["long_break_every"] == 4

    response = client.patch(
        "/api/v1/settings/pomodoro",
        json={"focus_minutes": 45, "short_break_minutes": 10},
    )
    assert response.status_code == 200
    assert response.json()["focus_minutes"] == 45
    assert response.json()["short_break_minutes"] == 10
    assert client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 0}).status_code == 422
