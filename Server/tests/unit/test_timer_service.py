from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.entities import SessionStatus, TimerPhase, TimerState
from app.services.timers import TimerService
from tests.fakes import FakeUnitOfWork


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def test_focus_timer_state_loop_closes_linked_session() -> None:
    clock = FakeClock(datetime(2026, 8, 16, 9, 0, tzinfo=UTC))
    unit_of_work = FakeUnitOfWork()
    service = TimerService(lambda: unit_of_work, clock)

    timer = service.start(phase=TimerPhase.FOCUS, title="Read chapter")
    linked_session = unit_of_work.sessions.get_by_timer_id(timer.id)
    assert linked_session is not None
    assert linked_session.status is SessionStatus.ACTIVE
    assert linked_session.duration_seconds == 0

    clock.current += timedelta(seconds=10)
    paused = service.pause(timer.id)
    assert paused.state is TimerState.PAUSED
    assert paused.remaining_seconds == 1490

    clock.current += timedelta(seconds=30)
    resumed = service.resume(timer.id)
    assert resumed.state is TimerState.RUNNING
    assert resumed.expected_end_at == clock.current + timedelta(seconds=1490)

    clock.current += timedelta(seconds=20)
    completed = service.complete(timer.id)
    assert completed.state is TimerState.COMPLETED
    assert completed.remaining_seconds == 0
    assert service.complete(timer.id) is completed
    assert linked_session.status is SessionStatus.COMPLETED
    assert linked_session.ended_at == clock.current
    assert linked_session.duration_seconds == 30


def test_get_active_reconciles_expired_timer_at_expected_end() -> None:
    clock = FakeClock(datetime(2026, 8, 16, 9, 0, tzinfo=UTC))
    unit_of_work = FakeUnitOfWork()
    service = TimerService(lambda: unit_of_work, clock)
    timer = service.start(phase=TimerPhase.FOCUS)
    expected_end = timer.expected_end_at

    clock.current = expected_end + timedelta(seconds=20)

    assert service.get_active() is None
    assert timer.state is TimerState.COMPLETED
    assert timer.completed_at == expected_end
    linked_session = unit_of_work.sessions.get_by_timer_id(timer.id)
    assert linked_session is not None
    assert linked_session.ended_at == expected_end
    assert linked_session.duration_seconds == timer.duration_seconds


def test_cancel_is_idempotent_and_cancels_focus_session() -> None:
    clock = FakeClock(datetime(2026, 8, 16, 9, 0, tzinfo=UTC))
    unit_of_work = FakeUnitOfWork()
    service = TimerService(lambda: unit_of_work, clock)
    timer = service.start(phase=TimerPhase.FOCUS)

    clock.current += timedelta(seconds=5)
    cancelled = service.cancel(timer.id)

    assert cancelled.state is TimerState.CANCELLED
    assert service.cancel(timer.id) is cancelled
    linked_session = unit_of_work.sessions.get_by_timer_id(timer.id)
    assert linked_session is not None
    assert linked_session.status is SessionStatus.CANCELLED
    assert linked_session.duration_seconds == 5
