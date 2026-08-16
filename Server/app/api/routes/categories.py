from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_clock, get_unit_of_work_factory
from app.core.clock import Clock
from app.domain.repositories import UnitOfWorkFactory
from app.schemas.categories import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.categories import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

UnitOfWorkDependency = Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)]
ClockDependency = Annotated[Clock, Depends(get_clock)]


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[CategoryResponse]:
    categories = CategoryService(unit_of_work_factory, clock).list(include_deleted=include_deleted)
    return [CategoryResponse.model_validate(category) for category in categories]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> CategoryResponse:
    category = CategoryService(unit_of_work_factory, clock).create(
        name=payload.name, color=payload.color
    )
    return CategoryResponse.model_validate(category)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
    include_deleted: Annotated[bool, Query()] = False,
) -> CategoryResponse:
    category = CategoryService(unit_of_work_factory, clock).get(
        category_id, include_deleted=include_deleted
    )
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    payload: CategoryUpdate,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> CategoryResponse:
    category = CategoryService(unit_of_work_factory, clock).update(
        category_id,
        name=payload.name,
        color=payload.color,
        fields_set=payload.model_fields_set,
    )
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> Response:
    CategoryService(unit_of_work_factory, clock).delete(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{category_id}/restore", response_model=CategoryResponse)
def restore_category(
    category_id: str,
    unit_of_work_factory: UnitOfWorkDependency,
    clock: ClockDependency,
) -> CategoryResponse:
    category = CategoryService(unit_of_work_factory, clock).restore(category_id)
    return CategoryResponse.model_validate(category)
