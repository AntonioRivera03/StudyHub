from datetime import datetime
from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from app.schemas.common import ApiModel

CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]
CategoryColor = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)
]


class CategoryCreate(ApiModel):
    name: CategoryName
    color: CategoryColor | None = None


class CategoryUpdate(ApiModel):
    name: CategoryName | None = None
    color: CategoryColor | None = None

    @model_validator(mode="after")
    def name_cannot_be_null(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class CategoryResponse(ApiModel):
    id: str
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
