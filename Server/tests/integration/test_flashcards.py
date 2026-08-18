import sqlite3
from datetime import timedelta
from uuid import uuid4

from tests.conftest import ApiContext


def create_deck(api_context: ApiContext, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Calculus identities"}
    payload.update(overrides)
    response = api_context.client.post("/api/v1/decks", json=payload)
    assert response.status_code == 201
    return response.json()


def create_card(
    api_context: ApiContext, deck_id: str, front: str, **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {
        "front_markdown": front,
        "back_markdown": f"Answer for {front}",
    }
    payload.update(overrides)
    response = api_context.client.post(f"/api/v1/decks/{deck_id}/cards", json=payload)
    assert response.status_code == 201
    return response.json()


def test_deck_card_authoring_ordering_and_restore_rules(api_context: ApiContext) -> None:
    client = api_context.client
    category = client.post("/api/v1/categories", json={"name": "Mathematics"}).json()
    deck = create_deck(
        api_context,
        name="  Calculus  ",
        description="Core identities",
        category_id=category["id"],
    )
    deck_id = str(deck["id"])
    assert deck["name"] == "Calculus"

    last = create_card(api_context, deck_id, "last", position=5)
    first = create_card(api_context, deck_id, "  preserved source  ", position=0)
    appended = create_card(api_context, deck_id, "appended")
    assert first["front_markdown"] == "  preserved source  "
    assert appended["position"] == 6
    assert "category_id" not in first
    assert first["schedule"] == {
        "repetitions": 0,
        "interval_days": 0,
        "ease_factor": 2.5,
        "due_at": api_context.clock.current.isoformat().replace("+00:00", "Z"),
        "last_reviewed_at": None,
    }
    assert [item["id"] for item in client.get(f"/api/v1/decks/{deck_id}/cards").json()] == [
        first["id"],
        last["id"],
        appended["id"],
    ]
    assert (
        client.post(
            f"/api/v1/decks/{deck_id}/cards",
            json={"front_markdown": "x", "back_markdown": "y", "category_id": category["id"]},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/cards/{first['id']}", json={"schedule": {"repetitions": 9}}
        ).status_code
        == 422
    )

    assert client.delete(f"/api/v1/cards/{first['id']}").status_code == 204
    assert client.delete(f"/api/v1/decks/{deck_id}").status_code == 204
    assert client.get(f"/api/v1/cards/{last['id']}").status_code == 404
    assert client.get(f"/api/v1/cards/{last['id']}?include_deleted=true").status_code == 200
    assert client.get(f"/api/v1/decks/{deck_id}/cards").status_code == 404
    assert len(client.get(f"/api/v1/decks/{deck_id}/cards?include_deleted=true").json()) == 3
    assert client.post(f"/api/v1/cards/{first['id']}/restore").status_code == 409

    restored_deck = client.post(f"/api/v1/decks/{deck_id}/restore")
    assert restored_deck.status_code == 200
    assert restored_deck.json()["active_card_count"] == 2
    assert restored_deck.json()["due_card_count"] == 2
    assert client.post(f"/api/v1/cards/{first['id']}/restore").status_code == 200
    assert client.post(f"/api/v1/cards/{first['id']}/restore").status_code == 409


def test_due_selection_uses_boundary_and_deterministic_order(api_context: ApiContext) -> None:
    deck = create_deck(api_context)
    deck_id = str(deck["id"])
    at_boundary = create_card(api_context, deck_id, "boundary", position=2)
    oldest = create_card(api_context, deck_id, "oldest", position=9)
    future = create_card(api_context, deck_id, "future", position=0)
    now = api_context.clock.current

    with sqlite3.connect(api_context.database_path) as connection:
        connection.execute(
            "UPDATE flashcards SET due_at = ? WHERE id = ?",
            (
                (now - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f"),
                oldest["id"],
            ),
        )
        connection.execute(
            "UPDATE flashcards SET due_at = ? WHERE id = ?",
            (
                (now + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S.%f"),
                future["id"],
            ),
        )
        connection.commit()

    due = api_context.client.get(f"/api/v1/decks/{deck_id}/due-cards").json()
    assert [card["id"] for card in due] == [oldest["id"], at_boundary["id"]]
    assert api_context.client.get(f"/api/v1/decks/{deck_id}").json()["due_card_count"] == 2

    api_context.clock.current += timedelta(seconds=1)
    due = api_context.client.get(f"/api/v1/decks/{deck_id}/due-cards").json()
    assert [card["id"] for card in due] == [oldest["id"], at_boundary["id"], future["id"]]


def test_review_retry_lifecycle_snapshot_and_dashboard_aggregation(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    category = client.post("/api/v1/categories", json={"name": "Original"}).json()
    other_category = client.post("/api/v1/categories", json={"name": "Other"}).json()
    deck = create_deck(api_context, category_id=category["id"])
    deck_id = str(deck["id"])
    first = create_card(api_context, deck_id, "first", position=0)
    second = create_card(api_context, deck_id, "second", position=1)

    started = client.post("/api/v1/reviews", json={"deck_id": deck_id})
    assert started.status_code == 201
    progress = started.json()
    review_id = progress["session"]["id"]
    assert progress["session"]["category_id_snapshot"] == category["id"]
    assert progress["next_card"]["id"] == first["id"]
    assert progress["remaining_due_card_count"] == 2
    assert client.get("/api/v1/sessions").json() == []
    assert client.post("/api/v1/reviews", json={"deck_id": deck_id}).status_code == 409
    assert client.delete(f"/api/v1/decks/{deck_id}").status_code == 409

    client.patch(f"/api/v1/decks/{deck_id}", json={"category_id": other_category["id"]})
    assert (
        client.get(f"/api/v1/reviews/{review_id}").json()["session"]["category_id_snapshot"]
        == category["id"]
    )

    command_id = str(uuid4())
    payload = {"command_id": command_id, "card_id": first["id"], "rating": "good"}
    assert (
        client.post(
            f"/api/v1/reviews/{review_id}/ratings",
            json={"command_id": str(uuid4()), "card_id": second["id"], "rating": "good"},
        ).status_code
        == 409
    )
    rated = client.post(f"/api/v1/reviews/{review_id}/ratings", json=payload)
    retried = client.post(f"/api/v1/reviews/{review_id}/ratings", json=payload)
    assert rated.status_code == retried.status_code == 200
    assert retried.json()["event"]["id"] == rated.json()["event"]["id"]
    assert retried.json()["event"]["sequence"] == 1
    assert retried.json()["progress"]["reviewed_card_count"] == 1
    assert retried.json()["progress"]["next_card"]["id"] == second["id"]
    assert client.get(f"/api/v1/cards/{first['id']}").json()["schedule"]["repetitions"] == 1
    assert (
        client.post(
            f"/api/v1/reviews/{review_id}/ratings",
            json={"command_id": command_id, "card_id": first["id"], "rating": "easy"},
        ).status_code
        == 409
    )

    second_rating = client.post(
        f"/api/v1/reviews/{review_id}/ratings",
        json={"command_id": str(uuid4()), "card_id": second["id"], "rating": "hard"},
    )
    assert second_rating.status_code == 200
    assert second_rating.json()["event"]["sequence"] == 2
    assert second_rating.json()["progress"]["next_card"] is None

    api_context.clock.current += timedelta(seconds=125)
    completed = client.post(f"/api/v1/reviews/{review_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["session"]["duration_seconds"] == 125
    assert client.post(f"/api/v1/reviews/{review_id}/complete").status_code == 200
    assert client.post(f"/api/v1/reviews/{review_id}/abandon").status_code == 409
    assert client.get("/api/v1/reviews/active").json() is None

    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["today_completed_review_minutes"] == 2
    assert summary["today_completed_review_session_count"] == 1
    assert summary["today_reviewed_card_count"] == 2
    assert summary["today_completed_session_count"] == 0
    assert client.get("/api/v1/sessions").json() == []

    assert client.delete(f"/api/v1/reviews/{review_id}").status_code == 204
    deleted_summary = client.get("/api/v1/dashboard/summary").json()
    assert deleted_summary["today_completed_review_session_count"] == 0
    assert deleted_summary["today_reviewed_card_count"] == 0
    assert client.get(f"/api/v1/reviews/{review_id}").status_code == 404
    assert client.get(f"/api/v1/reviews/{review_id}?include_deleted=true").status_code == 200
    assert client.post(f"/api/v1/reviews/{review_id}/restore").status_code == 200
    assert client.get("/api/v1/dashboard/summary").json()["today_reviewed_card_count"] == 2


def test_abandon_is_a_distinct_idempotent_terminal_state(api_context: ApiContext) -> None:
    deck = create_deck(api_context)
    deck_id = str(deck["id"])
    create_card(api_context, deck_id, "card")
    started = api_context.client.post("/api/v1/reviews", json={"deck_id": deck_id}).json()
    review_id = started["session"]["id"]

    api_context.clock.current += timedelta(seconds=10)
    abandoned = api_context.client.post(f"/api/v1/reviews/{review_id}/abandon")

    assert abandoned.status_code == 200
    assert abandoned.json()["session"]["status"] == "abandoned"
    assert abandoned.json()["session"]["duration_seconds"] == 10
    assert api_context.client.post(f"/api/v1/reviews/{review_id}/abandon").status_code == 200
    assert api_context.client.post(f"/api/v1/reviews/{review_id}/complete").status_code == 409
    summary = api_context.client.get("/api/v1/dashboard/summary").json()
    assert summary["today_completed_review_session_count"] == 0
    assert summary["today_reviewed_card_count"] == 0


def test_card_mutations_conflict_during_active_review_and_succeed_after_abandon(
    api_context: ApiContext,
) -> None:
    client = api_context.client
    deck = create_deck(api_context)
    deck_id = str(deck["id"])
    card = create_card(api_context, deck_id, "card", position=0)
    other = create_card(api_context, deck_id, "other", position=1)
    deleted = create_card(api_context, deck_id, "deleted", position=2)
    assert client.delete(f"/api/v1/cards/{deleted['id']}").status_code == 204

    started = client.post("/api/v1/reviews", json={"deck_id": deck_id})
    assert started.status_code == 201
    review_id = started.json()["session"]["id"]

    assert (
        client.post(
            f"/api/v1/decks/{deck_id}/cards",
            json={"front_markdown": "new", "back_markdown": "answer"},
        ).status_code
        == 409
    )
    assert (
        client.patch(f"/api/v1/cards/{card['id']}", json={"front_markdown": "edited"}).status_code
        == 409
    )
    assert client.delete(f"/api/v1/cards/{other['id']}").status_code == 409
    assert client.post(f"/api/v1/cards/{deleted['id']}/restore").status_code == 409

    assert client.post(f"/api/v1/reviews/{review_id}/abandon").status_code == 200

    assert (
        client.post(
            f"/api/v1/decks/{deck_id}/cards",
            json={"front_markdown": "new", "back_markdown": "answer"},
        ).status_code
        == 201
    )
    assert (
        client.patch(f"/api/v1/cards/{card['id']}", json={"front_markdown": "edited"}).status_code
        == 200
    )
    assert client.delete(f"/api/v1/cards/{other['id']}").status_code == 204
    assert client.post(f"/api/v1/cards/{deleted['id']}/restore").status_code == 200


def test_card_mutations_succeed_after_review_completion(api_context: ApiContext) -> None:
    client = api_context.client
    deck = create_deck(api_context)
    deck_id = str(deck["id"])
    card = create_card(api_context, deck_id, "card")

    started = client.post("/api/v1/reviews", json={"deck_id": deck_id})
    assert started.status_code == 201
    review_id = started.json()["session"]["id"]
    assert client.post(f"/api/v1/reviews/{review_id}/complete").status_code == 200

    assert (
        client.patch(f"/api/v1/cards/{card['id']}", json={"front_markdown": "edited"}).status_code
        == 200
    )
    assert client.delete(f"/api/v1/cards/{card['id']}").status_code == 204
    assert client.post(f"/api/v1/cards/{card['id']}/restore").status_code == 200


def test_flashcard_openapi_exposes_phase_two_contract(api_context: ApiContext) -> None:
    schema = api_context.client.get("/openapi.json").json()

    assert "/api/v1/decks/{deck_id}/due-cards" in schema["paths"]
    assert "/api/v1/reviews/{review_session_id}/ratings" in schema["paths"]
    assert "ScheduleSnapshotResponse" in schema["components"]["schemas"]
    dashboard_properties = schema["components"]["schemas"]["DashboardSummaryResponse"]["properties"]
    assert "today_completed_review_minutes" in dashboard_properties
    assert "today_reviewed_card_count" in dashboard_properties
