from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.timers import StudyFlowStateResponse, TimerResponse, TimerStart
from app.services.timers import TimerService

router = APIRouter(prefix="/timer", tags=["timer"])


@router.get("/active", response_model=TimerResponse | None)
def get_active_timer(
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse | None:
    timer = TimerService(unit_of_work_factory, clock).get_active()
    return TimerResponse.model_validate(timer) if timer else None


@router.get("/study-flow/active", response_model=StudyFlowStateResponse | None)
def get_active_study_flow(
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StudyFlowStateResponse | None:
    study_flow = TimerService(unit_of_work_factory, clock).get_active_study_flow()
    return StudyFlowStateResponse.model_validate(study_flow) if study_flow else None


@router.get("/study-flow/{session_id}", response_model=StudyFlowStateResponse)
def get_study_flow(
    session_id: str,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StudyFlowStateResponse:
    study_flow = TimerService(unit_of_work_factory, clock).get_study_flow(session_id)
    return StudyFlowStateResponse.model_validate(study_flow)


@router.post(
    "/study-flow/{session_id}/segments/{segment_index}/confirm",
    response_model=StudyFlowStateResponse,
)
def confirm_study_flow_segment(
    session_id: str,
    segment_index: int,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StudyFlowStateResponse:
    study_flow = TimerService(unit_of_work_factory, clock).confirm_study_flow_segment(
        session_id,
        segment_index,
    )
    return StudyFlowStateResponse.model_validate(study_flow)


@router.post("/start", response_model=TimerResponse, status_code=status.HTTP_201_CREATED)
def start_timer(
    payload: TimerStart,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse:
    timer = TimerService(unit_of_work_factory, clock).start(
        phase=payload.phase,
        category_id=payload.category_id,
        title=payload.title,
        study_flow_session_id=payload.study_flow_session_id,
        study_flow_segment_index=payload.study_flow_segment_index,
    )
    return TimerResponse.model_validate(timer)


@router.post("/{timer_id}/pause", response_model=TimerResponse)
def pause_timer(
    timer_id: str,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse:
    timer = TimerService(unit_of_work_factory, clock).pause(timer_id)
    return TimerResponse.model_validate(timer)


@router.post("/{timer_id}/resume", response_model=TimerResponse)
def resume_timer(
    timer_id: str,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse:
    timer = TimerService(unit_of_work_factory, clock).resume(timer_id)
    return TimerResponse.model_validate(timer)


@router.post("/{timer_id}/complete", response_model=TimerResponse)
def complete_timer(
    timer_id: str,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse:
    timer = TimerService(unit_of_work_factory, clock).complete(timer_id)
    return TimerResponse.model_validate(timer)


@router.post("/{timer_id}/cancel", response_model=TimerResponse)
def cancel_timer(
    timer_id: str,
    unit_of_work_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TimerResponse:
    timer = TimerService(unit_of_work_factory, clock).cancel(timer_id)
    return TimerResponse.model_validate(timer)
