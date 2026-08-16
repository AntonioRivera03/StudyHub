from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
    timezone_offset_minutes: Annotated[
        int,
        Query(
            ge=-840,
            le=840,
            description=(
                "Minutes from local time to UTC, matching JavaScript getTimezoneOffset(); "
                "defaults to UTC"
            ),
        ),
    ] = 0,
) -> DashboardSummaryResponse:
    summary = DashboardService(unit_of_work_factory, clock).summary(
        timezone_offset_minutes=timezone_offset_minutes
    )
    return DashboardSummaryResponse.model_validate(summary)
