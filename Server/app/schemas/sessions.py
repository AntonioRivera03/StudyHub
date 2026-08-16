from datetime import datetime
from typing import Annotated, Self

from pydantic import AfterValidator, StringConstraints, model_validator

from app.domain.entities import SessionSource, SessionStatus
from app.schemas.common import ApiModel, require_aware_utc

SessionTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Notes = Annotated[str, StringConstraints(max_length=10000)]
UtcDateTime = Annotated[datetime, AfterValidator(require_aware_utc)]


class StudySessionCreate(ApiModel):
    title: SessionTitle
    category_id: str | None = None
    started_at: UtcDateTime
    ended_at: UtcDateTime | None = None
    notes: Notes | None = None


class StudySessionUpdate(ApiModel):
    title: SessionTitle | None = None
    category_id: str | None = None
    started_at: UtcDateTime | None = None
    ended_at: UtcDateTime | None = None
    notes: Notes | None = None

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> Self:
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        if "started_at" in self.model_fields_set and self.started_at is None:
            raise ValueError("started_at cannot be null")
        return self


class StudySessionResponse(ApiModel):
    id: str
    title: str
    category_id: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    notes: str | None
    source: SessionSource
    status: SessionStatus
    timer_id: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
