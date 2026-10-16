from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TodoPriority


def _strip_non_blank(value: str | None) -> str | None:
    if value is None:
        return value
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: TodoPriority = TodoPriority.MEDIUM
    category: str = Field(default="General", min_length=1, max_length=50)
    due_date: date | None = None

    normalize_text = field_validator("title", "category")(_strip_non_blank)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    """Partial update: only the fields sent by the client are changed."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
    priority: TodoPriority | None = None
    category: str | None = Field(default=None, min_length=1, max_length=50)
    due_date: date | None = None

    normalize_text = field_validator("title", "category")(_strip_non_blank)


class TodoResponse(TodoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TodoStats(BaseModel):
    total: int
    active: int
    completed: int
    overdue: int
    due_today: int
    completion_rate: float
    by_priority: dict[str, int]
    by_category: dict[str, int]


class ClearCompletedResponse(BaseModel):
    deleted: int
