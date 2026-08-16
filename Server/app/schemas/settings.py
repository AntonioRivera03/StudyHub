from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiModel


class PomodoroSettingsUpdate(ApiModel):
    focus_minutes: int | None = Field(default=None, ge=1, le=180)
    short_break_minutes: int | None = Field(default=None, ge=1, le=60)
    long_break_minutes: int | None = Field(default=None, ge=1, le=120)
    long_break_every: int | None = Field(default=None, ge=1, le=12)


class PomodoroSettingsResponse(ApiModel):
    focus_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    long_break_every: int
    created_at: datetime
    updated_at: datetime
