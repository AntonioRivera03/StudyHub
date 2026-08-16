import math
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.domain.entities import (
    PomodoroSettings,
    SessionSource,
    SessionStatus,
    StudySession,
    Timer,
    TimerPhase,
    TimerState,
)
from app.domain.repositories import UnitOfWork, UnitOfWorkFactory
from app.services.settings import get_or_create_pomodoro_settings


class TimerService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def get_active(self) -> Timer | None:
        with self._unit_of_work_factory() as unit_of_work:
            timer = unit_of_work.timers.get_active()
            if timer is None:
                return None
            now = self._clock.now()
            if timer.state is TimerState.RUNNING and timer.expected_end_at <= now:
                self._complete(unit_of_work, timer, timer.expected_end_at)
                unit_of_work.commit()
                return None
            return timer

    def start(
        self,
        *,
        phase: TimerPhase,
        category_id: str | None = None,
        title: str | None = None,
    ) -> Timer:
        with self._unit_of_work_factory() as unit_of_work:
            now = self._clock.now()
            active_timer = unit_of_work.timers.get_active()
            if active_timer is not None:
                if active_timer.state is TimerState.RUNNING and active_timer.expected_end_at <= now:
                    self._complete(unit_of_work, active_timer, active_timer.expected_end_at)
                    unit_of_work.flush()
                else:
                    raise ConflictError("Another timer is already active")
            if phase is not TimerPhase.FOCUS and (category_id is not None or title is not None):
                raise ValidationError("Category and title are only supported for focus timers")
            if category_id is not None and unit_of_work.categories.get(category_id) is None:
                raise ValidationError("Category not found")

            settings = get_or_create_pomodoro_settings(unit_of_work, self._clock)
            duration_seconds = self._duration_minutes(settings, phase) * 60
            timer = Timer(
                id=str(uuid4()),
                phase=phase,
                state=TimerState.RUNNING,
                category_id=category_id,
                title=title,
                duration_seconds=duration_seconds,
                remaining_seconds=duration_seconds,
                started_at=now,
                expected_end_at=now + timedelta(seconds=duration_seconds),
                created_at=now,
                updated_at=now,
            )
            unit_of_work.timers.add(timer)
            if phase is TimerPhase.FOCUS:
                unit_of_work.flush()
                unit_of_work.sessions.add(
                    StudySession(
                        id=str(uuid4()),
                        title=title or "Focus session",
                        category_id=category_id,
                        started_at=now,
                        ended_at=None,
                        duration_seconds=0,
                        notes=None,
                        source=SessionSource.POMODORO,
                        status=SessionStatus.ACTIVE,
                        timer_id=timer.id,
                        created_at=now,
                        updated_at=now,
                    )
                )
            unit_of_work.commit()
            return timer

    def pause(self, timer_id: str) -> Timer:
        with self._unit_of_work_factory() as unit_of_work:
            timer = self._get_timer(unit_of_work, timer_id)
            if timer.state is not TimerState.RUNNING:
                raise ConflictError("Only a running timer can be paused")
            now = self._clock.now()
            if timer.expected_end_at <= now:
                self._complete(unit_of_work, timer, timer.expected_end_at)
            else:
                timer.remaining_seconds = max(
                    0, math.ceil((timer.expected_end_at - now).total_seconds())
                )
                timer.state = TimerState.PAUSED
                timer.paused_at = now
                timer.updated_at = now
                unit_of_work.timers.save(timer)
            unit_of_work.commit()
            return timer

    def resume(self, timer_id: str) -> Timer:
        with self._unit_of_work_factory() as unit_of_work:
            timer = self._get_timer(unit_of_work, timer_id)
            if timer.state is not TimerState.PAUSED:
                raise ConflictError("Only a paused timer can be resumed")
            now = self._clock.now()
            timer.state = TimerState.RUNNING
            timer.expected_end_at = now + timedelta(seconds=timer.remaining_seconds)
            timer.paused_at = None
            timer.updated_at = now
            unit_of_work.timers.save(timer)
            unit_of_work.commit()
            return timer

    def complete(self, timer_id: str) -> Timer:
        with self._unit_of_work_factory() as unit_of_work:
            timer = self._get_timer(unit_of_work, timer_id)
            if timer.state is TimerState.COMPLETED:
                return timer
            if timer.state is TimerState.CANCELLED:
                raise ConflictError("A cancelled timer cannot be completed")
            self._complete(unit_of_work, timer, self._clock.now())
            unit_of_work.commit()
            return timer

    def cancel(self, timer_id: str) -> Timer:
        with self._unit_of_work_factory() as unit_of_work:
            timer = self._get_timer(unit_of_work, timer_id)
            if timer.state is TimerState.CANCELLED:
                return timer
            if timer.state is TimerState.COMPLETED:
                raise ConflictError("A completed timer cannot be cancelled")
            now = self._clock.now()
            timer.remaining_seconds = self._remaining_seconds_at(timer, now)
            active_seconds = timer.duration_seconds - timer.remaining_seconds
            timer.state = TimerState.CANCELLED
            timer.cancelled_at = now
            timer.paused_at = None
            timer.updated_at = now
            unit_of_work.timers.save(timer)
            self._close_focus_session(
                unit_of_work,
                timer,
                SessionStatus.CANCELLED,
                now,
                active_seconds,
            )
            unit_of_work.commit()
            return timer

    @staticmethod
    def _duration_minutes(settings: PomodoroSettings, phase: TimerPhase) -> int:
        if phase is TimerPhase.FOCUS:
            return settings.focus_minutes
        if phase is TimerPhase.SHORT_BREAK:
            return settings.short_break_minutes
        return settings.long_break_minutes

    @staticmethod
    def _get_timer(unit_of_work: UnitOfWork, timer_id: str) -> Timer:
        timer = unit_of_work.timers.get(timer_id)
        if timer is None:
            raise NotFoundError("Timer not found")
        return timer

    @staticmethod
    def _complete(unit_of_work: UnitOfWork, timer: Timer, completed_at: datetime) -> None:
        remaining_seconds = TimerService._remaining_seconds_at(timer, completed_at)
        active_seconds = timer.duration_seconds - remaining_seconds
        timer.state = TimerState.COMPLETED
        timer.remaining_seconds = 0
        timer.completed_at = completed_at
        timer.paused_at = None
        timer.updated_at = completed_at
        unit_of_work.timers.save(timer)
        TimerService._close_focus_session(
            unit_of_work,
            timer,
            SessionStatus.COMPLETED,
            completed_at,
            active_seconds,
        )

    @staticmethod
    def _remaining_seconds_at(timer: Timer, at: datetime) -> int:
        if timer.state is TimerState.PAUSED:
            return timer.remaining_seconds
        return min(
            timer.duration_seconds,
            max(0, math.ceil((timer.expected_end_at - at).total_seconds())),
        )

    @staticmethod
    def _close_focus_session(
        unit_of_work: UnitOfWork,
        timer: Timer,
        status: SessionStatus,
        ended_at: datetime,
        duration_seconds: int,
    ) -> None:
        if timer.phase is not TimerPhase.FOCUS:
            return
        study_session = unit_of_work.sessions.get_by_timer_id(timer.id)
        if study_session is None or study_session.status is not SessionStatus.ACTIVE:
            return
        if ended_at <= study_session.started_at:
            ended_at = study_session.started_at + timedelta(microseconds=1)
        study_session.status = status
        study_session.ended_at = ended_at
        study_session.duration_seconds = duration_seconds
        study_session.updated_at = ended_at
        unit_of_work.sessions.save(study_session)
