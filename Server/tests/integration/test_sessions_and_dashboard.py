from datetime import timedelta

from tests.conftest import ApiContext


def test_manual_session_validation_and_soft_delete(api_context: ApiContext) -> None:
    client = api_context.client
    start = api_context.clock.current
    invalid_response = client.post(
        "/api/v1/sessions",
        json={
            "title": "Invalid",
            "started_at": start.isoformat(),
            "ended_at": (start - timedelta(minutes=1)).isoformat(),
        },
    )
    assert invalid_response.status_code == 422
    assert invalid_response.json()["error"]["code"] == "validation_error"

    created = client.post(
        "/api/v1/sessions",
        json={
            "title": "Review notes",
            "started_at": start.isoformat(),
            "ended_at": (start + timedelta(minutes=30)).isoformat(),
            "notes": "Chapter 2",
        },
    )
    assert created.status_code == 201
    session_id = created.json()["id"]
    assert created.json()["source"] == "manual"
    assert created.json()["status"] == "completed"
    assert created.json()["duration_seconds"] == 1800

    updated = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"ended_at": (start + timedelta(minutes=45)).isoformat()},
    )
    assert updated.status_code == 200
    assert updated.json()["duration_seconds"] == 2700

    assert (
        client.patch(f"/api/v1/sessions/{session_id}", json={"started_at": None}).status_code == 422
    )

    assert client.delete(f"/api/v1/sessions/{session_id}").status_code == 204
    assert client.get("/api/v1/sessions").json() == []
    assert len(client.get("/api/v1/sessions?include_deleted=true").json()) == 1
    restored = client.post(f"/api/v1/sessions/{session_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["deleted_at"] is None


def test_active_session_cannot_be_deleted(api_context: ApiContext) -> None:
    response = api_context.client.post(
        "/api/v1/sessions",
        json={
            "title": "In progress",
            "started_at": api_context.clock.current.isoformat(),
        },
    )
    session_id = response.json()["id"]
    assert response.json()["duration_seconds"] == 0

    delete_response = api_context.client.delete(f"/api/v1/sessions/{session_id}")

    assert delete_response.status_code == 409
    assert delete_response.json()["error"]["code"] == "conflict"
    assert api_context.client.get(f"/api/v1/sessions/{session_id}").status_code == 200


def test_dashboard_summarizes_local_day(api_context: ApiContext) -> None:
    client = api_context.client
    start = api_context.clock.current
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    client.post("/api/v1/timer/start", json={"phase": "focus", "title": "Focus"})
    api_context.clock.current += timedelta(seconds=61)

    manual_response = client.post(
        "/api/v1/sessions",
        json={
            "title": "Manual",
            "started_at": start.isoformat(),
            "ended_at": (start + timedelta(minutes=20)).isoformat(),
        },
    )
    assert manual_response.status_code == 201

    response = client.get("/api/v1/dashboard/summary?timezone_offset_minutes=0")
    assert response.status_code == 200
    summary = response.json()
    assert summary["today_completed_focus_minutes"] == 1
    assert summary["today_completed_session_count"] == 2
    assert summary["active_timer"] is None
    assert len(summary["recent_sessions"]) == 2
