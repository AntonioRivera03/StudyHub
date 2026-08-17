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


def test_study_flow_logs_one_session_from_first_start_to_final_completion(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    client.patch(
        "/api/v1/settings/pomodoro",
        json={
            "focus_minutes": 1,
            "short_break_minutes": 1,
            "long_break_minutes": 1,
        },
    )
    phases = [
        "focus",
        "short_break",
        "focus",
        "short_break",
        "focus",
        "long_break",
    ]
    study_flow_session_id = None
    first_started_at = None
    final_completed_at = None

    for index, phase in enumerate(phases):
        payload: dict[str, object] = {
            "phase": phase,
            "study_flow_segment_index": index,
        }
        if study_flow_session_id is not None:
            payload["study_flow_session_id"] = study_flow_session_id
        if index == 0:
            payload["title"] = "Exam review flow"

        started_response = client.post("/api/v1/timer/start", json=payload)
        assert started_response.status_code == 201
        timer = started_response.json()
        if index == 0:
            study_flow_session_id = timer["study_flow_session_id"]
            first_started_at = timer["started_at"]
        assert timer["study_flow_session_id"] == study_flow_session_id
        assert timer["study_flow_segment_index"] == index

        api_context.clock.current += timedelta(seconds=20 if phase == "focus" else 5)
        completed_response = client.post(f"/api/v1/timer/{timer['id']}/complete")
        assert completed_response.status_code == 200
        final_completed_at = completed_response.json()["completed_at"]

        current_session = client.get(f"/api/v1/sessions/{study_flow_session_id}").json()
        if index < len(phases) - 1:
            assert current_session["status"] == "active"
            assert current_session["ended_at"] is None

    sessions = client.get("/api/v1/sessions").json()
    assert len(sessions) == 1
    study_flow_session = sessions[0]
    assert study_flow_session["id"] == study_flow_session_id
    assert study_flow_session["source"] == "study_flow"
    assert study_flow_session["status"] == "completed"
    assert study_flow_session["title"] == "Exam review flow"
    assert study_flow_session["timer_id"] is None
    assert study_flow_session["started_at"] == first_started_at
    assert study_flow_session["ended_at"] == final_completed_at
    assert study_flow_session["duration_seconds"] == 60

    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["today_completed_focus_minutes"] == 1
    assert summary["today_completed_session_count"] == 1


def test_cancelling_study_flow_segment_cancels_session_and_allows_new_flow(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    first_timer = client.post(
        "/api/v1/timer/start",
        json={
            "phase": "focus",
            "title": "Retry flow",
            "study_flow_segment_index": 0,
        },
    ).json()
    session_id = first_timer["study_flow_session_id"]

    api_context.clock.current += timedelta(seconds=10)
    assert client.post(f"/api/v1/timer/{first_timer['id']}/cancel").status_code == 200
    session = client.get(f"/api/v1/sessions/{session_id}").json()
    assert session["status"] == "cancelled"
    assert session["ended_at"] == api_context.clock.current.isoformat().replace("+00:00", "Z")
    assert session["duration_seconds"] == 0

    finished_session_retry = client.post(
        "/api/v1/timer/start",
        json={
            "phase": "focus",
            "study_flow_session_id": session_id,
            "study_flow_segment_index": 0,
        },
    )
    assert finished_session_retry.status_code == 409

    new_flow = client.post(
        "/api/v1/timer/start",
        json={
            "phase": "focus",
            "study_flow_segment_index": 0,
        },
    )
    assert new_flow.status_code == 201
    assert new_flow.json()["study_flow_session_id"] != session_id


def test_expired_study_flow_segment_requires_confirmation_before_next_start(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    timer = client.post(
        "/api/v1/timer/start",
        json={"phase": "focus", "study_flow_segment_index": 0},
    ).json()
    session_id = timer["study_flow_session_id"]
    api_context.clock.current += timedelta(seconds=61)

    recovered_flow = client.get("/api/v1/timer/study-flow/active")
    assert recovered_flow.status_code == 200
    assert recovered_flow.json()["session_id"] == session_id
    assert recovered_flow.json()["current_segment_index"] == 0
    assert recovered_flow.json()["awaiting_confirmation"] is True
    assert recovered_flow.json()["active_timer"] is None

    blocked_start = client.post(
        "/api/v1/timer/start",
        json={
            "phase": "short_break",
            "study_flow_session_id": session_id,
            "study_flow_segment_index": 1,
        },
    )
    assert blocked_start.status_code == 409

    confirmed = client.post(f"/api/v1/timer/study-flow/{session_id}/segments/0/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["current_segment_index"] == 1
    assert confirmed.json()["awaiting_confirmation"] is False

    next_timer = client.post(
        "/api/v1/timer/start",
        json={
            "phase": "short_break",
            "study_flow_session_id": session_id,
            "study_flow_segment_index": 1,
        },
    )
    assert next_timer.status_code == 201


def test_cancelling_expired_study_flow_timer_preserves_completed_segment(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    client.patch("/api/v1/settings/pomodoro", json={"focus_minutes": 1})
    timer = client.post(
        "/api/v1/timer/start",
        json={"phase": "focus", "study_flow_segment_index": 0},
    ).json()
    api_context.clock.current += timedelta(seconds=61)

    response = client.post(f"/api/v1/timer/{timer['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["state"] == "completed"
    assert response.json()["study_flow_confirmed_at"] is None
    session = client.get(f"/api/v1/sessions/{timer['study_flow_session_id']}").json()
    assert session["status"] == "active"
    assert session["duration_seconds"] == 60
