from datetime import datetime
from typing import Annotated, Self

from pydantic import AfterValidator, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.common import ApiModel

DeckName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
DeckDescription = Annotated[str, StringConstraints(max_length=2000)]
Position = Annotated[int, Field(ge=0)]


def validate_card_markdown(value: str) -> str:
    if len(value) > 20000:
        raise ValueError("card markdown must have at most 20000 characters")
    if not value.strip():
        raise ValueError("card markdown must contain non-whitespace content")
    return value


CardMarkdown = Annotated[str, AfterValidator(validate_card_markdown)]


class FlashcardDeckCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    name: DeckName
    description: DeckDescription | None = None
    category_id: str | None = None


class FlashcardDeckUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    name: DeckName | None = None
    description: DeckDescription | None = None
    category_id: str | None = None

    @model_validator(mode="after")
    def name_cannot_be_null(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class FlashcardDeckResponse(ApiModel):
    id: str
    name: str
    description: str | None
    category_id: str | None
    active_card_count: int
    due_card_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class FlashcardCreate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    front_markdown: CardMarkdown
    back_markdown: CardMarkdown
    position: Position | None = None


class FlashcardUpdate(ApiModel):
    model_config = ConfigDict(extra="forbid")

    front_markdown: CardMarkdown | None = None
    back_markdown: CardMarkdown | None = None
    position: Position | None = None

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> Self:
        for field_name in ("front_markdown", "back_markdown", "position"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class ScheduleSnapshotResponse(ApiModel):
    repetitions: int
    interval_days: int
    ease_factor: float
    due_at: datetime
    last_reviewed_at: datetime | None


class FlashcardResponse(ApiModel):
    id: str
    deck_id: str
    front_markdown: str
    back_markdown: str
    position: int
    schedule: ScheduleSnapshotResponse
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
