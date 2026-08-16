from uuid import uuid4

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError
from app.domain.entities import Category
from app.domain.repositories import UnitOfWorkFactory


class CategoryService:
    def __init__(self, unit_of_work_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock

    def list(self, *, include_deleted: bool = False) -> list[Category]:
        with self._unit_of_work_factory() as unit_of_work:
            return unit_of_work.categories.list(include_deleted=include_deleted)

    def get(self, category_id: str, *, include_deleted: bool = False) -> Category:
        with self._unit_of_work_factory() as unit_of_work:
            category = unit_of_work.categories.get(category_id, include_deleted=include_deleted)
            if category is None:
                raise NotFoundError("Category not found")
            return category

    def create(self, *, name: str, color: str | None) -> Category:
        now = self._clock.now()
        category = Category(
            id=str(uuid4()),
            name=name,
            color=color,
            created_at=now,
            updated_at=now,
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.categories.add(category)
            unit_of_work.commit()
        return category

    def update(
        self,
        category_id: str,
        *,
        name: str | None,
        color: str | None,
        fields_set: set[str],
    ) -> Category:
        with self._unit_of_work_factory() as unit_of_work:
            category = unit_of_work.categories.get(category_id)
            if category is None:
                raise NotFoundError("Category not found")
            if "name" in fields_set and name is not None:
                category.name = name
            if "color" in fields_set:
                category.color = color
            category.updated_at = self._clock.now()
            unit_of_work.categories.save(category)
            unit_of_work.commit()
            return category

    def delete(self, category_id: str) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            category = unit_of_work.categories.get(category_id)
            if category is None:
                raise NotFoundError("Category not found")
            now = self._clock.now()
            category.deleted_at = now
            category.updated_at = now
            unit_of_work.categories.save(category)
            unit_of_work.commit()

    def restore(self, category_id: str) -> Category:
        with self._unit_of_work_factory() as unit_of_work:
            category = unit_of_work.categories.get(category_id, include_deleted=True)
            if category is None:
                raise NotFoundError("Category not found")
            if category.deleted_at is None:
                raise ConflictError("Category is not deleted")
            category.deleted_at = None
            category.updated_at = self._clock.now()
            unit_of_work.categories.save(category)
            unit_of_work.commit()
            return category
