from datetime import timedelta

from tests.conftest import ApiContext


def test_timer_start_pause_resume_complete_loop(api_context: ApiContext) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    category = client.post("/api/v1/categories", json={"name": "Physics"}).json()

    started_response = client.post(
        "/api/v1/timer/start",
        json={"phase": "focus", "title": "Waves", "category_id": category["id"]},
    )
    assert started_response.status_code == 201
    timer_id = started_response.json()["id"]
    assert started_response.json()["duration_seconds"] == 60
    assert client.post("/api/v1/timer/start", json={"phase": "short_break"}).status_code == 409

    api_context.clock.current += timedelta(seconds=10)
    paused = client.post(f"/api/v1/timer/{timer_id}/pause").json()
    assert paused["state"] == "paused"
    assert paused["remaining_seconds"] == 50

    api_context.clock.current += timedelta(seconds=10)
    resumed = client.post(f"/api/v1/timer/{timer_id}/resume").json()
    assert resumed["state"] == "running"

    api_context.clock.current += timedelta(seconds=20)
    completed = client.post(f"/api/v1/timer/{timer_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["state"] == "completed"
    assert client.post(f"/api/v1/timer/{timer_id}/complete").status_code == 200
    assert client.get("/api/v1/timer/active").json() is None

    sessions = client.get("/api/v1/sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["source"] == "pomodoro"
    assert sessions[0]["status"] == "completed"
    assert sessions[0]["title"] == "Waves"
    assert sessions[0]["duration_seconds"] == 30
    updated_session = client.patch(
        f"/api/v1/sessions/{sessions[0]['id']}", json={"notes": "Retained duration"}
    ).json()
    assert updated_session["duration_seconds"] == 30


def test_active_timer_expiration_reconciliation(api_context: ApiContext) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    started = client.post("/api/v1/timer/start", json={"phase": "focus"}).json()
    expected_end = started["expected_end_at"]

    api_context.clock.current += timedelta(seconds=61)

    assert client.get("/api/v1/timer/active").json() is None
    session = client.get("/api/v1/sessions").json()[0]
    assert session["status"] == "completed"
    assert session["ended_at"] == expected_end
    assert session["duration_seconds"] == 60


def test_early_completion_uses_elapsed_time_in_dashboard(api_context: ApiContext) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 2})
    timer = client.post("/api/v1/timer/start", json={"phase": "focus"}).json()

    api_context.clock.current += timedelta(seconds=75)
    assert client.post(f"/api/v1/timer/{timer['id']}/complete").status_code == 200

    session = client.get("/api/v1/sessions").json()[0]
    assert session["duration_seconds"] == 75
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["today_completed_focus_minutes"] == 1


def test_start_reconciles_expired_timer_before_conflict_check(api_context: ApiContext) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    first_timer = client.post("/api/v1/timer/start", json={"phase": "focus"}).json()
    api_context.clock.current += timedelta(seconds=61)

    second_response = client.post("/api/v1/timer/start", json={"phase": "short_break"})

    assert second_response.status_code == 201
    assert second_response.json()["id"] != first_timer["id"]
    sessions = client.get("/api/v1/sessions").json()
    assert sessions[0]["status"] == "completed"
    assert sessions[0]["duration_seconds"] == 60


def test_break_timer_does_not_create_session(api_context: ApiContext) -> None:
    response = api_context.client.post("/api/v1/timer/start", json={"phase": "short_break"})
    assert response.status_code == 201
    assert api_context.client.get("/api/v1/sessions").json() == []
