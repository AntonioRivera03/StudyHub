import math
from dataclasses import dataclass
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

STUDY_FLOW_PHASES = (
    TimerPhase.FOCUS,
    TimerPhase.SHORT_BREAK,
    TimerPhase.FOCUS,
    TimerPhase.SHORT_BREAK,
    TimerPhase.FOCUS,
    TimerPhase.LONG_BREAK,
)


@dataclass(slots=True)
class StudyFlowState:
    session_id: str
    title: str
    category_id: str | None
    status: SessionStatus
    current_segment_index: int
    awaiting_confirmation: bool
    active_timer: Timer | None


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

    def get_active_study_flow(self) -> StudyFlowState | None:
        self.get_active()
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get_active_by_source(SessionSource.STUDY_FLOW)
            if study_session is None:
                return None
            return self._study_flow_state(unit_of_work, study_session)

    def get_study_flow(self, session_id: str) -> StudyFlowState:
        self.get_active()
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id)
            if study_session is None or study_session.source is not SessionSource.STUDY_FLOW:
                raise NotFoundError("StudyFlow session not found")
            return self._study_flow_state(unit_of_work, study_session)

    def confirm_study_flow_segment(self, session_id: str, segment_index: int) -> StudyFlowState:
        with self._unit_of_work_factory() as unit_of_work:
            study_session = unit_of_work.sessions.get(session_id)
            if study_session is None or study_session.source is not SessionSource.STUDY_FLOW:
                raise NotFoundError("StudyFlow session not found")
            timers = unit_of_work.timers.list_by_study_flow_session_id(session_id)
            timer = next(
                (
                    item
                    for item in timers
                    if item.study_flow_segment_index == segment_index
                    and item.state is TimerState.COMPLETED
                    and item.study_flow_confirmed_at is None
                ),
                None,
            )
            if timer is None:
                raise ConflictError("StudyFlow segment is not awaiting confirmation")
            now = self._clock.now()
            timer.study_flow_confirmed_at = now
            timer.updated_at = now
            unit_of_work.timers.save(timer)
            unit_of_work.commit()
            return self._study_flow_state(unit_of_work, study_session)

    def start(
        self,
        *,
        phase: TimerPhase,
        category_id: str | None = None,
        title: str | None = None,
        study_flow_session_id: str | None = None,
        study_flow_segment_index: int | None = None,
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

            study_flow_session = self._prepare_study_flow_session(
                unit_of_work,
                segment_index=study_flow_segment_index,
                session_id=study_flow_session_id,
                phase=phase,
                category_id=category_id,
                title=title,
                started_at=now,
            )
            if study_flow_session is not None and phase is TimerPhase.FOCUS:
                category_id = study_flow_session.category_id
                title = study_flow_session.title

            settings = get_or_create_pomodoro_settings(unit_of_work, self._clock)
            duration_seconds = self._duration_minutes(settings, phase) * 60
            timer = Timer(
                id=str(uuid4()),
                phase=phase,
                state=TimerState.RUNNING,
                category_id=category_id,
                title=title,
                study_flow_session_id=(
                    study_flow_session.id if study_flow_session is not None else None
                ),
                study_flow_segment_index=study_flow_segment_index,
                duration_seconds=duration_seconds,
                remaining_seconds=duration_seconds,
                started_at=now,
                expected_end_at=now + timedelta(seconds=duration_seconds),
                created_at=now,
                updated_at=now,
            )
            unit_of_work.timers.add(timer)
            if phase is TimerPhase.FOCUS and study_flow_session is None:
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

    @staticmethod
    def _prepare_study_flow_session(
        unit_of_work: UnitOfWork,
        *,
        segment_index: int | None,
        session_id: str | None,
        phase: TimerPhase,
        category_id: str | None,
        title: str | None,
        started_at: datetime,
    ) -> StudySession | None:
        if segment_index is None:
            if session_id is not None:
                raise ValidationError(
                    "study_flow_segment_index is required with study_flow_session_id"
                )
            return None
        if not 0 <= segment_index < len(STUDY_FLOW_PHASES):
            raise ValidationError("Invalid StudyFlow segment")
        if STUDY_FLOW_PHASES[segment_index] is not phase:
            raise ValidationError("Timer phase does not match the StudyFlow segment")

        if session_id is None:
            if segment_index != 0:
                raise ValidationError("study_flow_session_id is required after the first segment")
            if unit_of_work.sessions.get_active_by_source(SessionSource.STUDY_FLOW) is not None:
                raise ConflictError("Another StudyFlow session is already active")
            new_study_session = StudySession(
                id=str(uuid4()),
                title=title or "StudyFlow session",
                category_id=category_id,
                started_at=started_at,
                ended_at=None,
                duration_seconds=0,
                notes=None,
                source=SessionSource.STUDY_FLOW,
                status=SessionStatus.ACTIVE,
                timer_id=None,
                created_at=started_at,
                updated_at=started_at,
            )
            unit_of_work.sessions.add(new_study_session)
            unit_of_work.flush()
            return new_study_session

        existing_study_session = unit_of_work.sessions.get(session_id)
        if (
            existing_study_session is None
            or existing_study_session.source is not SessionSource.STUDY_FLOW
        ):
            raise NotFoundError("StudyFlow session not found")
        if existing_study_session.status is not SessionStatus.ACTIVE:
            raise ConflictError("StudyFlow session is already finished")

        completed_segments = {
            timer.study_flow_segment_index
            for timer in unit_of_work.timers.list_by_study_flow_session_id(session_id)
            if timer.state is TimerState.COMPLETED and timer.study_flow_confirmed_at is not None
        }
        expected_segment = 0
        while expected_segment in completed_segments:
            expected_segment += 1
        if segment_index != expected_segment:
            raise ConflictError("StudyFlow segments must be completed in order")
        return existing_study_session

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
            now = self._clock.now()
            completed_at = (
                timer.expected_end_at
                if timer.state is TimerState.RUNNING and timer.expected_end_at <= now
                else now
            )
            self._complete(
                unit_of_work,
                timer,
                completed_at,
                confirm_study_flow=True,
            )
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
            if timer.state is TimerState.RUNNING and timer.expected_end_at <= now:
                self._complete(unit_of_work, timer, timer.expected_end_at)
                unit_of_work.commit()
                return timer
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
    def _complete(
        unit_of_work: UnitOfWork,
        timer: Timer,
        completed_at: datetime,
        *,
        confirm_study_flow: bool = False,
    ) -> None:
        remaining_seconds = TimerService._remaining_seconds_at(timer, completed_at)
        active_seconds = timer.duration_seconds - remaining_seconds
        timer.state = TimerState.COMPLETED
        timer.remaining_seconds = 0
        timer.completed_at = completed_at
        if timer.study_flow_session_id is not None and confirm_study_flow:
            timer.study_flow_confirmed_at = completed_at
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
        if timer.study_flow_session_id is not None:
            TimerService._update_study_flow_session(
                unit_of_work,
                timer,
                status,
                ended_at,
                duration_seconds,
            )
            return
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

    @staticmethod
    def _update_study_flow_session(
        unit_of_work: UnitOfWork,
        timer: Timer,
        timer_status: SessionStatus,
        completed_at: datetime,
        active_seconds: int,
    ) -> None:
        study_session = unit_of_work.sessions.get(timer.study_flow_session_id or "")
        if study_session is None or study_session.status is not SessionStatus.ACTIVE:
            return
        if timer_status is SessionStatus.CANCELLED:
            if completed_at <= study_session.started_at:
                completed_at = study_session.started_at + timedelta(microseconds=1)
            study_session.status = SessionStatus.CANCELLED
            study_session.ended_at = completed_at
            study_session.updated_at = completed_at
            unit_of_work.sessions.save(study_session)
            return

        if timer.phase is TimerPhase.FOCUS:
            study_session.duration_seconds += active_seconds
        if timer.study_flow_segment_index == len(STUDY_FLOW_PHASES) - 1:
            if completed_at <= study_session.started_at:
                completed_at = study_session.started_at + timedelta(microseconds=1)
            study_session.status = SessionStatus.COMPLETED
            study_session.ended_at = completed_at
        study_session.updated_at = completed_at
        unit_of_work.sessions.save(study_session)

    @staticmethod
    def _study_flow_state(unit_of_work: UnitOfWork, study_session: StudySession) -> StudyFlowState:
        timers = unit_of_work.timers.list_by_study_flow_session_id(study_session.id)
        confirmed_segments = {
            timer.study_flow_segment_index
            for timer in timers
            if timer.state is TimerState.COMPLETED and timer.study_flow_confirmed_at is not None
        }
        current_segment_index = 0
        while current_segment_index in confirmed_segments:
            current_segment_index += 1
        current_timer = next(
            (
                timer
                for timer in reversed(timers)
                if timer.study_flow_segment_index == current_segment_index
                and timer.state is not TimerState.CANCELLED
            ),
            None,
        )
        awaiting_confirmation = bool(
            current_timer
            and current_timer.state is TimerState.COMPLETED
            and current_timer.study_flow_confirmed_at is None
        )
        active_timer = (
            current_timer
            if current_timer and current_timer.state in {TimerState.RUNNING, TimerState.PAUSED}
            else None
        )
        return StudyFlowState(
            session_id=study_session.id,
            title=study_session.title,
            category_id=study_session.category_id,
            status=study_session.status,
            current_segment_index=current_segment_index,
            awaiting_confirmation=awaiting_confirmation,
            active_timer=active_timer,
        )
