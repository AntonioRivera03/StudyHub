from typing import cast

from fastapi import Request

from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory


def get_unit_of_work_factory(request: Request) -> UnitOfWorkFactory:
    return cast(UnitOfWorkFactory, request.app.state.unit_of_work_factory)


def get_clock(request: Request) -> Clock:
    return cast(Clock, request.app.state.clock)
