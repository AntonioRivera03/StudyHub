from datetime import datetime
from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from app.domain.entities import SessionStatus, TimerPhase, TimerState
from app.schemas.common import ApiModel

TimerTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class TimerStart(ApiModel):
    phase: TimerPhase
    category_id: str | None = None
    title: TimerTitle | None = None
    study_flow_session_id: str | None = None
    study_flow_segment_index: int | None = Field(default=None, ge=0, le=5)

    @model_validator(mode="after")
    def focus_metadata_only(self) -> Self:
        if self.phase is not TimerPhase.FOCUS and (
            self.category_id is not None or self.title is not None
        ):
            raise ValueError("category_id and title are only supported for focus timers")
        if self.study_flow_session_id is not None and self.study_flow_segment_index is None:
            raise ValueError("study_flow_segment_index is required with study_flow_session_id")
        if (
            self.study_flow_segment_index is not None
            and self.study_flow_segment_index > 0
            and self.study_flow_session_id is None
        ):
            raise ValueError("study_flow_session_id is required after the first segment")
        return self


class TimerResponse(ApiModel):
    id: str
    phase: TimerPhase
    state: TimerState
    category_id: str | None
    title: str | None
    study_flow_session_id: str | None
    study_flow_segment_index: int | None
    study_flow_confirmed_at: datetime | None
    duration_seconds: int
    remaining_seconds: int
    started_at: datetime
    expected_end_at: datetime
    paused_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StudyFlowStateResponse(ApiModel):
    session_id: str
    title: str
    category_id: str | None
    status: SessionStatus
    current_segment_index: int
    awaiting_confirmation: bool
    active_timer: TimerResponse | None
