from uuid import uuid4

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.domain.entities import Flashcard, FlashcardDeck, ScheduleSnapshot
from app.domain.repositories import UnitOfWork, UnitOfWorkFactory


class FlashcardDeckService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def list(self, *, include_deleted: bool = False) -> list[FlashcardDeck]:
        with self._unit_of_work_factory() as unit_of_work:
            return unit_of_work.decks.list(self._clock.now(), include_deleted=include_deleted)

    def get(self, deck_id: str, *, include_deleted: bool = False) -> FlashcardDeck:
        with self._unit_of_work_factory() as unit_of_work:
            deck = unit_of_work.decks.get(
                deck_id, self._clock.now(), include_deleted=include_deleted
            )
            if deck is None:
                raise NotFoundError("Flashcard deck not found")
            return deck

    def create(
        self, *, name: str, description: str | None, category_id: str | None
    ) -> FlashcardDeck:
        now = self._clock.now()
        with self._unit_of_work_factory() as unit_of_work:
            self._validate_category(unit_of_work, category_id)
            deck = FlashcardDeck(
                id=str(uuid4()),
                name=name,
                description=description,
                category_id=category_id,
                active_card_count=0,
                due_card_count=0,
                created_at=now,
                updated_at=now,
            )
            unit_of_work.decks.add(deck)
            unit_of_work.commit()
            return deck

    def update(self, deck_id: str, *, changes: dict[str, str | None]) -> FlashcardDeck:
        with self._unit_of_work_factory() as unit_of_work:
            deck = unit_of_work.decks.get(deck_id, self._clock.now())
            if deck is None:
                raise NotFoundError("Flashcard deck not found")
            if "category_id" in changes:
                self._validate_category(unit_of_work, changes["category_id"])
            for field_name, value in changes.items():
                setattr(deck, field_name, value)
            deck.updated_at = self._clock.now()
            unit_of_work.decks.save(deck)
            unit_of_work.commit()
            updated = unit_of_work.decks.get(deck_id, self._clock.now())
            if updated is None:
                raise NotFoundError("Flashcard deck not found")
            return updated

    def delete(self, deck_id: str) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            deck = unit_of_work.decks.get(deck_id, self._clock.now())
            if deck is None:
                raise NotFoundError("Flashcard deck not found")
            if unit_of_work.review_sessions.get_active_for_deck(deck_id) is not None:
                raise ConflictError("A deck with an in-progress review cannot be deleted")
            now = self._clock.now()
            deck.deleted_at = now
            deck.updated_at = now
            unit_of_work.decks.save(deck)
            unit_of_work.commit()

    def restore(self, deck_id: str) -> FlashcardDeck:
        with self._unit_of_work_factory() as unit_of_work:
            deck = unit_of_work.decks.get(deck_id, self._clock.now(), include_deleted=True)
            if deck is None:
                raise NotFoundError("Flashcard deck not found")
            if deck.deleted_at is None:
                raise ConflictError("Flashcard deck is not deleted")
            deck.deleted_at = None
            deck.updated_at = self._clock.now()
            unit_of_work.decks.save(deck)
            unit_of_work.commit()
            restored = unit_of_work.decks.get(deck_id, self._clock.now())
            if restored is None:
                raise NotFoundError("Flashcard deck not found")
            return restored

    @staticmethod
    def _validate_category(unit_of_work: UnitOfWork, category_id: str | None) -> None:
        if category_id is not None and unit_of_work.categories.get(category_id) is None:
            raise ValidationError("Category not found")


class FlashcardService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def list_by_deck(self, deck_id: str, *, include_deleted: bool = False) -> list[Flashcard]:
        with self._unit_of_work_factory() as unit_of_work:
            self._require_deck(unit_of_work, deck_id, include_deleted=include_deleted)
            return unit_of_work.cards.list_by_deck(deck_id, include_deleted=include_deleted)

    def get(self, card_id: str, *, include_deleted: bool = False) -> Flashcard:
        with self._unit_of_work_factory() as unit_of_work:
            card = unit_of_work.cards.get(card_id, include_deleted=include_deleted)
            if card is None:
                raise NotFoundError("Flashcard not found")
            return card

    def create(
        self,
        deck_id: str,
        *,
        front_markdown: str,
        back_markdown: str,
        position: int | None,
    ) -> Flashcard:
        with self._unit_of_work_factory() as unit_of_work:
            self._require_deck(unit_of_work, deck_id)
            self._ensure_deck_has_no_active_review(unit_of_work, deck_id, operation="created")
            if position is None:
                maximum = unit_of_work.cards.max_position(deck_id)
                position = 0 if maximum is None else maximum + 1
            now = self._clock.now()
            card = Flashcard(
                id=str(uuid4()),
                deck_id=deck_id,
                front_markdown=front_markdown,
                back_markdown=back_markdown,
                position=position,
                schedule=ScheduleSnapshot(
                    repetitions=0,
                    interval_days=0,
                    ease_factor=2.5,
                    due_at=now,
                    last_reviewed_at=None,
                ),
                created_at=now,
                updated_at=now,
            )
            unit_of_work.cards.add(card)
            unit_of_work.commit()
            return card

    def update(self, card_id: str, *, changes: dict[str, str | int]) -> Flashcard:
        with self._unit_of_work_factory() as unit_of_work:
            card = unit_of_work.cards.get(card_id)
            if card is None:
                raise NotFoundError("Flashcard not found")
            self._ensure_deck_has_no_active_review(unit_of_work, card.deck_id, operation="updated")
            for field_name, value in changes.items():
                setattr(card, field_name, value)
            card.updated_at = self._clock.now()
            unit_of_work.cards.save(card)
            unit_of_work.commit()
            return card

    def delete(self, card_id: str) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            card = unit_of_work.cards.get(card_id)
            if card is None:
                raise NotFoundError("Flashcard not found")
            self._ensure_deck_has_no_active_review(unit_of_work, card.deck_id, operation="deleted")
            now = self._clock.now()
            card.deleted_at = now
            card.updated_at = now
            unit_of_work.cards.save(card)
            unit_of_work.commit()

    def restore(self, card_id: str) -> Flashcard:
        with self._unit_of_work_factory() as unit_of_work:
            card = unit_of_work.cards.get(card_id, include_deleted=True)
            if card is None:
                raise NotFoundError("Flashcard not found")
            if card.deleted_at is None:
                raise ConflictError("Flashcard is not deleted")
            if unit_of_work.decks.get(card.deck_id, self._clock.now()) is None:
                raise ConflictError("The parent flashcard deck is deleted")
            self._ensure_deck_has_no_active_review(unit_of_work, card.deck_id, operation="restored")
            card.deleted_at = None
            card.updated_at = self._clock.now()
            unit_of_work.cards.save(card)
            unit_of_work.commit()
            return card

    def list_due(self, deck_id: str) -> list[Flashcard]:
        with self._unit_of_work_factory() as unit_of_work:
            self._require_deck(unit_of_work, deck_id)
            return unit_of_work.cards.list_due(deck_id, self._clock.now())

    @staticmethod
    def _ensure_deck_has_no_active_review(
        unit_of_work: UnitOfWork, deck_id: str, *, operation: str
    ) -> None:
        if unit_of_work.review_sessions.get_active_for_deck(deck_id) is not None:
            raise ConflictError(f"Cards cannot be {operation} in a deck with an in-progress review")

    def _require_deck(
        self, unit_of_work: UnitOfWork, deck_id: str, *, include_deleted: bool = False
    ) -> FlashcardDeck:
        deck = unit_of_work.decks.get(deck_id, self._clock.now(), include_deleted=include_deleted)
        if deck is None:
            raise NotFoundError("Flashcard deck not found")
        return deck
