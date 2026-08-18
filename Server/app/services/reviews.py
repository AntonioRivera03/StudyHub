from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError
from app.domain.entities import (
    Flashcard,
    ReviewEvent,
    ReviewRating,
    ReviewSession,
    ReviewStatus,
)
from app.domain.repositories import UnitOfWork, UnitOfWorkFactory
from app.domain.scheduling import RATING_QUALITY, apply_sm2


@dataclass(slots=True)
class ReviewProgress:
    session: ReviewSession
    reviewed_card_count: int
    remaining_due_card_count: int
    next_card: Flashcard | None


@dataclass(slots=True)
class ReviewRatingResult:
    event: ReviewEvent
    progress: ReviewProgress


class ReviewService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def list(self, *, include_deleted: bool = False) -> list[ReviewSession]:
        with self._unit_of_work_factory() as unit_of_work:
            return unit_of_work.review_sessions.list(include_deleted=include_deleted)

    def start(self, deck_id: str) -> ReviewProgress:
        with self._unit_of_work_factory() as unit_of_work:
            now = self._clock.now()
            deck = unit_of_work.decks.get(deck_id, now)
            if deck is None:
                raise NotFoundError("Flashcard deck not found")
            if unit_of_work.review_sessions.get_active() is not None:
                raise ConflictError("Another review session is already in progress")
            if not unit_of_work.cards.list_due(deck_id, now):
                raise ConflictError("The flashcard deck has no due cards")
            review_session = ReviewSession(
                id=str(uuid4()),
                deck_id=deck.id,
                category_id_snapshot=deck.category_id,
                status=ReviewStatus.IN_PROGRESS,
                started_at=now,
                ended_at=None,
                duration_seconds=0,
                created_at=now,
                updated_at=now,
            )
            unit_of_work.review_sessions.add(review_session)
            unit_of_work.commit()
            return self._progress(unit_of_work, review_session, now)

    def get_active(self) -> ReviewProgress | None:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get_active()
            if review_session is None:
                return None
            return self._progress(unit_of_work, review_session, self._clock.now())

    def get(self, review_session_id: str, *, include_deleted: bool = False) -> ReviewProgress:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get(
                review_session_id, include_deleted=include_deleted
            )
            if review_session is None:
                raise NotFoundError("Review session not found")
            return self._progress(unit_of_work, review_session, self._clock.now())

    def next_card(self, review_session_id: str) -> Flashcard | None:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get(
                review_session_id, include_deleted=True
            )
            if review_session is None:
                raise NotFoundError("Review session not found")
            if (
                review_session.deleted_at is not None
                or review_session.status is not ReviewStatus.IN_PROGRESS
            ):
                raise ConflictError("Review session is not in progress")
            due_cards = unit_of_work.cards.list_due_excluding_review(
                review_session.deck_id, review_session.id, self._clock.now()
            )
            return due_cards[0] if due_cards else None

    def rate(
        self,
        review_session_id: str,
        *,
        command_id: str,
        card_id: str,
        rating: ReviewRating,
    ) -> ReviewRatingResult:
        try:
            with self._unit_of_work_factory() as unit_of_work:
                existing = unit_of_work.review_events.get_by_command_id(command_id)
                if existing is not None:
                    self._validate_retry(existing, review_session_id, card_id, rating)
                    review_session = self._get_review_for_retry(unit_of_work, review_session_id)
                    return ReviewRatingResult(
                        event=existing,
                        progress=self._progress(unit_of_work, review_session, self._clock.now()),
                    )

                found_session = unit_of_work.review_sessions.get(
                    review_session_id, include_deleted=True
                )
                if found_session is None:
                    raise NotFoundError("Review session not found")
                review_session = found_session
                if (
                    review_session.deleted_at is not None
                    or review_session.status is not ReviewStatus.IN_PROGRESS
                ):
                    raise ConflictError("Review session is not in progress")
                now = self._clock.now()
                due_cards = unit_of_work.cards.list_due_excluding_review(
                    review_session.deck_id, review_session.id, now
                )
                if not due_cards or due_cards[0].id != card_id:
                    raise ConflictError("The card is not the review session's next card")

                card = due_cards[0]
                previous_schedule = card.schedule
                new_schedule = apply_sm2(previous_schedule, rating, now)
                event = ReviewEvent(
                    id=str(uuid4()),
                    command_id=command_id,
                    review_session_id=review_session.id,
                    card_id=card.id,
                    sequence=unit_of_work.review_events.next_sequence(review_session.id),
                    rating=rating,
                    quality=RATING_QUALITY[rating],
                    reviewed_at=now,
                    previous_schedule=previous_schedule,
                    new_schedule=new_schedule,
                )
                card.schedule = new_schedule
                card.updated_at = now
                review_session.updated_at = now
                unit_of_work.review_events.add(event)
                unit_of_work.cards.save(card)
                unit_of_work.review_sessions.save(review_session)
                unit_of_work.commit()
                return ReviewRatingResult(
                    event=event,
                    progress=self._progress(unit_of_work, review_session, now),
                )
        except ConflictError:
            # A concurrent identical command may have committed after the first lookup.
            with self._unit_of_work_factory() as unit_of_work:
                existing = unit_of_work.review_events.get_by_command_id(command_id)
                if existing is not None:
                    self._validate_retry(existing, review_session_id, card_id, rating)
                    review_session = self._get_review_for_retry(unit_of_work, review_session_id)
                    return ReviewRatingResult(
                        event=existing,
                        progress=self._progress(unit_of_work, review_session, self._clock.now()),
                    )
            raise

    def complete(self, review_session_id: str) -> ReviewProgress:
        return self._finish(review_session_id, ReviewStatus.COMPLETED)

    def abandon(self, review_session_id: str) -> ReviewProgress:
        return self._finish(review_session_id, ReviewStatus.ABANDONED)

    def delete(self, review_session_id: str) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get(review_session_id)
            if review_session is None:
                raise NotFoundError("Review session not found")
            if review_session.status is ReviewStatus.IN_PROGRESS:
                raise ConflictError("An in-progress review session cannot be deleted")
            now = self._clock.now()
            review_session.deleted_at = now
            review_session.updated_at = now
            unit_of_work.review_sessions.save(review_session)
            unit_of_work.commit()

    def restore(self, review_session_id: str) -> ReviewProgress:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get(
                review_session_id, include_deleted=True
            )
            if review_session is None:
                raise NotFoundError("Review session not found")
            if review_session.deleted_at is None:
                raise ConflictError("Review session is not deleted")
            review_session.deleted_at = None
            review_session.updated_at = self._clock.now()
            unit_of_work.review_sessions.save(review_session)
            unit_of_work.commit()
            return self._progress(unit_of_work, review_session, self._clock.now())

    def _finish(self, review_session_id: str, target_status: ReviewStatus) -> ReviewProgress:
        with self._unit_of_work_factory() as unit_of_work:
            review_session = unit_of_work.review_sessions.get(review_session_id)
            if review_session is None:
                raise NotFoundError("Review session not found")
            if review_session.status is target_status:
                return self._progress(unit_of_work, review_session, self._clock.now())
            if review_session.status is not ReviewStatus.IN_PROGRESS:
                raise ConflictError("Review session has a different terminal status")
            now = self._clock.now()
            review_session.status = target_status
            review_session.ended_at = now
            review_session.duration_seconds = max(
                0, int((now - review_session.started_at).total_seconds())
            )
            review_session.updated_at = now
            unit_of_work.review_sessions.save(review_session)
            unit_of_work.commit()
            return self._progress(unit_of_work, review_session, now)

    @staticmethod
    def _validate_retry(
        event: ReviewEvent,
        review_session_id: str,
        card_id: str,
        rating: ReviewRating,
    ) -> None:
        if (
            event.review_session_id != review_session_id
            or event.card_id != card_id
            or event.rating is not rating
        ):
            raise ConflictError("Command ID was already used for a different rating")

    @staticmethod
    def _get_review_for_retry(unit_of_work: UnitOfWork, review_session_id: str) -> ReviewSession:
        review_session = unit_of_work.review_sessions.get(review_session_id, include_deleted=True)
        if review_session is None:
            raise NotFoundError("Review session not found")
        return review_session

    @staticmethod
    def _progress(
        unit_of_work: UnitOfWork, review_session: ReviewSession, now: datetime
    ) -> ReviewProgress:
        due_cards = unit_of_work.cards.list_due_excluding_review(
            review_session.deck_id, review_session.id, now
        )
        events = unit_of_work.review_events.list_by_session(review_session.id)
        next_card = (
            due_cards[0]
            if due_cards
            and review_session.status is ReviewStatus.IN_PROGRESS
            and review_session.deleted_at is None
            else None
        )
        return ReviewProgress(
            session=review_session,
            reviewed_card_count=len(events),
            remaining_due_card_count=len(due_cards),
            next_card=next_card,
        )
