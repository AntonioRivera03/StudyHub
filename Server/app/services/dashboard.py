from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from app.core.clock import Clock
from app.domain.entities import SessionSource, StudySession, Timer
from app.domain.repositories import UnitOfWorkFactory
from app.services.timers import TimerService


@dataclass(slots=True)
class DashboardSummary:
    today_completed_focus_minutes: int
    today_completed_session_count: int
    today_completed_review_minutes: int
    today_completed_review_session_count: int
    today_reviewed_card_count: int
    active_timer: Timer | None
    recent_sessions: list[StudySession]


class DashboardService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock
        self._timer_service = TimerService(unit_of_work_factory, clock)

    def summary(self, *, timezone_offset_minutes: int) -> DashboardSummary:
        active_timer = self._timer_service.get_active()
        start, end = self._day_boundaries(timezone_offset_minutes)
        with self._unit_of_work_factory() as unit_of_work:
            completed_sessions = unit_of_work.sessions.list_completed_between(start, end)
            focus_seconds = sum(
                study_session.duration_seconds
                for study_session in completed_sessions
                if study_session.source in {SessionSource.POMODORO, SessionSource.STUDY_FLOW}
            )
            completed_reviews = unit_of_work.review_sessions.list_completed_between(start, end)
            review_seconds = sum(
                review_session.duration_seconds for review_session in completed_reviews
            )
            return DashboardSummary(
                today_completed_focus_minutes=focus_seconds // 60,
                today_completed_session_count=sum(
                    study_session.source in {SessionSource.MANUAL, SessionSource.POMODORO}
                    for study_session in completed_sessions
                ),
                today_completed_review_minutes=review_seconds // 60,
                today_completed_review_session_count=len(completed_reviews),
                today_reviewed_card_count=unit_of_work.review_events.count_for_sessions(
                    {review_session.id for review_session in completed_reviews}
                ),
                active_timer=active_timer,
                recent_sessions=unit_of_work.sessions.list_recent(limit=5),
            )

    def _day_boundaries(self, timezone_offset_minutes: int) -> tuple[datetime, datetime]:
        offset = timedelta(minutes=timezone_offset_minutes)
        local_now = self._clock.now() - offset
        local_start = datetime.combine(local_now.date(), time.min, tzinfo=UTC)
        start = local_start + offset
        return start, start + timedelta(days=1)
