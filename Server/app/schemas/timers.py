from datetime import datetime
from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from app.domain.entities import TimerPhase, TimerState
from app.schemas.common import ApiModel

TimerTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class TimerStart(ApiModel):
    phase: TimerPhase
    category_id: str | None = None
    title: TimerTitle | None = None

    @model_validator(mode="after")
    def focus_metadata_only(self) -> Self:
        if self.phase is not TimerPhase.FOCUS and (
            self.category_id is not None or self.title is not None
        ):
            raise ValueError("category_id and title are only supported for focus timers")
        return self


class TimerResponse(ApiModel):
    id: str
    phase: TimerPhase
    state: TimerState
    category_id: str | None
    title: str | None
    duration_seconds: int
    remaining_seconds: int
    started_at: datetime
    expected_end_at: datetime
    paused_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
