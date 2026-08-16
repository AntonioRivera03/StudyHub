from app.core.clock import Clock
from app.domain.entities import PomodoroSettings
from app.domain.repositories import UnitOfWork, UnitOfWorkFactory


def get_or_create_pomodoro_settings(unit_of_work: UnitOfWork, clock: Clock) -> PomodoroSettings:
    settings = unit_of_work.pomodoro_settings.get()
    if settings is not None:
        return settings
    now = clock.now()
    settings = PomodoroSettings(
        focus_minutes=25,
        short_break_minutes=5,
        long_break_minutes=15,
        long_break_every=4,
        created_at=now,
        updated_at=now,
    )
    unit_of_work.pomodoro_settings.add(settings)
    return settings


class PomodoroSettingsService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def get(self) -> PomodoroSettings:
        with self._unit_of_work_factory() as unit_of_work:
            settings = get_or_create_pomodoro_settings(unit_of_work, self._clock)
            unit_of_work.commit()
            return settings

    def update(self, changes: dict[str, int]) -> PomodoroSettings:
        with self._unit_of_work_factory() as unit_of_work:
            settings = get_or_create_pomodoro_settings(unit_of_work, self._clock)
            for field_name, value in changes.items():
                setattr(settings, field_name, value)
            settings.updated_at = self._clock.now()
            unit_of_work.pomodoro_settings.save(settings)
            unit_of_work.commit()
            return settings
