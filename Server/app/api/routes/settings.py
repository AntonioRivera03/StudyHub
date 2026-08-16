from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.settings import PomodoroSettingsResponse, PomodoroSettingsUpdate
from app.services.settings import PomodoroSettingsService

router = APIRouter(prefix="/settings/pomodoro", tags=["settings"])


@router.get("", response_model=PomodoroSettingsResponse)
def get_pomodoro_settings(
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> PomodoroSettingsResponse:
    settings = PomodoroSettingsService(unit_of_work_factory, clock).get()
    return PomodoroSettingsResponse.model_validate(settings)


@router.patch("", response_model=PomodoroSettingsResponse)
def update_pomodoro_settings(
    payload: PomodoroSettingsUpdate,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> PomodoroSettingsResponse:
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    settings = PomodoroSettingsService(unit_of_work_factory, clock).update(changes)
    return PomodoroSettingsResponse.model_validate(settings)
