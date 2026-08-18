from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.flashcards import FlashcardResponse
from app.schemas.reviews import (
    ReviewProgressResponse,
    ReviewRatingCreate,
    ReviewRatingResultResponse,
    ReviewSessionResponse,
    ReviewStart,
)
from app.services.reviews import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])

UnitOfWorkDependency = Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)]
ClockDependency = Annotated[Clock, Depends(get_clock)]


@router.get("", response_model=list[ReviewSessionResponse])
def list_reviews(
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[ReviewSessionResponse]:
    review_sessions = ReviewService(unit_of_work_factory, clock).list(
        include_deleted=include_deleted
    )
    return [
        ReviewSessionResponse.model_validate(review_session) for review_session in review_sessions
    ]


@router.post("", response_model=ReviewProgressResponse, status_code=status.HTTP_201_CREATED)
def start_review(
    payload: ReviewStart,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewProgressResponse:
    progress = ReviewService(unit_of_work_factory, clock).start(str(payload.deck_id))
    return ReviewProgressResponse.model_validate(progress)


@router.get("/active", response_model=ReviewProgressResponse | None)
def get_active_review(
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewProgressResponse | None:
    progress = ReviewService(unit_of_work_factory, clock).get_active()
    return ReviewProgressResponse.model_validate(progress) if progress else None


@router.get("/{review_session_id}", response_model=ReviewProgressResponse)
def get_review(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> ReviewProgressResponse:
    progress = ReviewService(unit_of_work_factory, clock).get(
        review_session_id, include_deleted=include_deleted
    )
    return ReviewProgressResponse.model_validate(progress)


@router.get("/{review_session_id}/next", response_model=FlashcardResponse | None)
def get_next_review_card(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> FlashcardResponse | None:
    card = ReviewService(unit_of_work_factory, clock).next_card(review_session_id)
    return FlashcardResponse.model_validate(card) if card else None


@router.post("/{review_session_id}/ratings", response_model=ReviewRatingResultResponse)
def rate_review_card(
    review_session_id: str,
    payload: ReviewRatingCreate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewRatingResultResponse:
    result = ReviewService(unit_of_work_factory, clock).rate(
        review_session_id,
        command_id=str(payload.command_id),
        card_id=str(payload.card_id),
        rating=payload.rating,
    )
    return ReviewRatingResultResponse.model_validate(result)


@router.post("/{review_session_id}/complete", response_model=ReviewProgressResponse)
def complete_review(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewProgressResponse:
    progress = ReviewService(unit_of_work_factory, clock).complete(review_session_id)
    return ReviewProgressResponse.model_validate(progress)


@router.post("/{review_session_id}/abandon", response_model=ReviewProgressResponse)
def abandon_review(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewProgressResponse:
    progress = ReviewService(unit_of_work_factory, clock).abandon(review_session_id)
    return ReviewProgressResponse.model_validate(progress)


@router.delete("/{review_session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> Response:
    ReviewService(unit_of_work_factory, clock).delete(review_session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{review_session_id}/restore", response_model=ReviewProgressResponse)
def restore_review(
    review_session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> ReviewProgressResponse:
    progress = ReviewService(unit_of_work_factory, clock).restore(review_session_id)
    return ReviewProgressResponse.model_validate(progress)
