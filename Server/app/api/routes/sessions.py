from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.sessions import StudySessionCreate, StudySessionResponse, StudySessionUpdate
from app.services.sessions import StudySessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

UnitOfWorkDependency = Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)]
ClockDependency = Annotated[Clock, Depends(get_clock)]


@router.get("", response_model=list[StudySessionResponse])
def list_sessions(
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[StudySessionResponse]:
    sessions = StudySessionService(unit_of_work_factory, clock).list(
        include_deleted=include_deleted
    )
    return [StudySessionResponse.model_validate(study_session) for study_session in sessions]


@router.post("", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: StudySessionCreate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> StudySessionResponse:
    study_session = StudySessionService(unit_of_work_factory, clock).create(
        title=payload.title,
        category_id=payload.category_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        notes=payload.notes,
    )
    return StudySessionResponse.model_validate(study_session)


@router.get("/{session_id}", response_model=StudySessionResponse)
def get_session(
    session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> StudySessionResponse:
    study_session = StudySessionService(unit_of_work_factory, clock).get(
        session_id, include_deleted=include_deleted
    )
    return StudySessionResponse.model_validate(study_session)


@router.patch("/{session_id}", response_model=StudySessionResponse)
def update_session(
    session_id: str,
    payload: StudySessionUpdate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> StudySessionResponse:
    changes = payload.model_dump(exclude_unset=True)
    study_session = StudySessionService(unit_of_work_factory, clock).update(
        session_id, changes=changes
    )
    return StudySessionResponse.model_validate(study_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> Response:
    StudySessionService(unit_of_work_factory, clock).delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/restore", response_model=StudySessionResponse)
def restore_session(
    session_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> StudySessionResponse:
    study_session = StudySessionService(unit_of_work_factory, clock).restore(session_id)
    return StudySessionResponse.model_validate(study_session)
