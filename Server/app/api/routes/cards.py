from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.flashcards import FlashcardResponse, FlashcardUpdate
from app.services.flashcards import FlashcardService

router = APIRouter(prefix="/cards", tags=["flashcards"])

UnitOfWorkDependency = Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)]
ClockDependency = Annotated[Clock, Depends(get_clock)]


@router.get("/{card_id}", response_model=FlashcardResponse)
def get_card(
    card_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> FlashcardResponse:
    card = FlashcardService(unit_of_work_factory, clock).get(
        card_id, include_deleted=include_deleted
    )
    return FlashcardResponse.model_validate(card)


@router.patch("/{card_id}", response_model=FlashcardResponse)
def update_card(
    card_id: str,
    payload: FlashcardUpdate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardResponse:
    card = FlashcardService(unit_of_work_factory, clock).update(
        card_id, changes=payload.model_dump(exclude_unset=True)
    )
    return FlashcardResponse.model_validate(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> Response:
    FlashcardService(unit_of_work_factory, clock).delete(card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{card_id}/restore", response_model=FlashcardResponse)
def restore_card(
    card_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardResponse:
    card = FlashcardService(unit_of_work_factory, clock).restore(card_id)
    return FlashcardResponse.model_validate(card)
