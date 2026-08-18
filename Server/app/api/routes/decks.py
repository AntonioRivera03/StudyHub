from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.flashcards import (
    FlashcardCreate,
    FlashcardDeckCreate,
    FlashcardDeckResponse,
    FlashcardDeckUpdate,
    FlashcardResponse,
)
from app.services.flashcards import FlashcardDeckService, FlashcardService

router = APIRouter(prefix="/decks", tags=["flashcards"])

UnitOfWorkDependency = Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)]
ClockDependency = Annotated[Clock, Depends(get_clock)]


@router.get("", response_model=list[FlashcardDeckResponse])
def list_decks(
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[FlashcardDeckResponse]:
    decks = FlashcardDeckService(unit_of_work_factory, clock).list(include_deleted=include_deleted)
    return [FlashcardDeckResponse.model_validate(deck) for deck in decks]


@router.post("", response_model=FlashcardDeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck(
    payload: FlashcardDeckCreate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardDeckResponse:
    deck = FlashcardDeckService(unit_of_work_factory, clock).create(
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
    )
    return FlashcardDeckResponse.model_validate(deck)


@router.get("/{deck_id}", response_model=FlashcardDeckResponse)
def get_deck(
    deck_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> FlashcardDeckResponse:
    deck = FlashcardDeckService(unit_of_work_factory, clock).get(
        deck_id, include_deleted=include_deleted
    )
    return FlashcardDeckResponse.model_validate(deck)


@router.patch("/{deck_id}", response_model=FlashcardDeckResponse)
def update_deck(
    deck_id: str,
    payload: FlashcardDeckUpdate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardDeckResponse:
    deck = FlashcardDeckService(unit_of_work_factory, clock).update(
        deck_id, changes=payload.model_dump(exclude_unset=True)
    )
    return FlashcardDeckResponse.model_validate(deck)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(
    deck_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> Response:
    FlashcardDeckService(unit_of_work_factory, clock).delete(deck_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{deck_id}/restore", response_model=FlashcardDeckResponse)
def restore_deck(
    deck_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardDeckResponse:
    deck = FlashcardDeckService(unit_of_work_factory, clock).restore(deck_id)
    return FlashcardDeckResponse.model_validate(deck)


@router.get("/{deck_id}/cards", response_model=list[FlashcardResponse])
def list_cards(
    deck_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[FlashcardResponse]:
    cards = FlashcardService(unit_of_work_factory, clock).list_by_deck(
        deck_id, include_deleted=include_deleted
    )
    return [FlashcardResponse.model_validate(card) for card in cards]


@router.post(
    "/{deck_id}/cards", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED
)
def create_card(
    deck_id: str,
    payload: FlashcardCreate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardResponse:
    card = FlashcardService(unit_of_work_factory, clock).create(
        deck_id,
        front_markdown=payload.front_markdown,
        back_markdown=payload.back_markdown,
        position=payload.position,
    )
    return FlashcardResponse.model_validate(card)


@router.get("/{deck_id}/due-cards", response_model=list[FlashcardResponse])
def list_due_cards(
    deck_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> list[FlashcardResponse]:
    cards = FlashcardService(unit_of_work_factory, clock).list_due(deck_id)
    return [FlashcardResponse.model_validate(card) for card in cards]
