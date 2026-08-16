from app.schemas.common import ApiModel
from app.schemas.sessions import StudySessionResponse
from app.schemas.timers import TimerResponse


class DashboardSummaryResponse(ApiModel):
    today_completed_focus_minutes: int
    today_completed_session_count: int
    active_timer: TimerResponse | None
    recent_sessions: list[StudySessionResponse]
