from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Todo, TodoPriority
from app.schemas import ClearCompletedResponse, TodoCreate, TodoResponse, TodoStats, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["Todos"])

PRIORITY_RANK = case(
    (Todo.priority == TodoPriority.HIGH, 0),
    (Todo.priority == TodoPriority.MEDIUM, 1),
    else_=2,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _get_or_404(db: Session, todo_id: int) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    return todo


def _set_completed(todo: Todo, completed: bool) -> None:
    todo.completed = completed
    todo.completed_at = datetime.now(timezone.utc) if completed else None


@router.get("", response_model=list[TodoResponse])
def list_todos(
    status_filter: Literal["all", "active", "completed", "overdue", "today"] = Query(
        "all", alias="status"
    ),
    priority: TodoPriority | None = None,
    category: str | None = None,
    search: str | None = Query(None, max_length=100),
    sort: Literal["created", "due_date", "priority", "title"] = "created",
    db: Session = Depends(get_db),
):
    """List todos with optional status, priority, category and text filters."""
    query = select(Todo)
    today = _today()

    if status_filter == "active":
        query = query.where(Todo.completed.is_(False))
    elif status_filter == "completed":
        query = query.where(Todo.completed.is_(True))
    elif status_filter == "overdue":
        query = query.where(Todo.completed.is_(False), Todo.due_date < today)
    elif status_filter == "today":
        query = query.where(Todo.due_date == today)

    if priority:
        query = query.where(Todo.priority == priority)
    if category:
        query = query.where(Todo.category == category)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern)))

    if sort == "due_date":
        # Todos without a due date go last
        query = query.order_by(Todo.due_date.is_(None), Todo.due_date, Todo.id.desc())
    elif sort == "priority":
        query = query.order_by(PRIORITY_RANK, Todo.id.desc())
    elif sort == "title":
        query = query.order_by(func.lower(Todo.title), Todo.id)
    else:
        query = query.order_by(Todo.id.desc())

    return db.scalars(query).all()


@router.get("/stats", response_model=TodoStats)
def todo_stats(db: Session = Depends(get_db)):
    """Aggregate counters for the dashboard cards."""
    today = _today()
    count = select(func.count(Todo.id))
    active = Todo.completed.is_(False)

    total = db.scalar(count) or 0
    completed = db.scalar(count.where(Todo.completed.is_(True))) or 0
    overdue = db.scalar(count.where(active, Todo.due_date < today)) or 0
    due_today = db.scalar(count.where(active, Todo.due_date == today)) or 0

    by_priority = {p.value: 0 for p in TodoPriority}
    rows = db.execute(
        select(Todo.priority, func.count(Todo.id)).where(active).group_by(Todo.priority)
    )
    for priority, n in rows:
        by_priority[priority.value] = n

    by_category = dict(
        db.execute(
            select(Todo.category, func.count(Todo.id))
            .group_by(Todo.category)
            .order_by(Todo.category)
        ).all()
    )

    return TodoStats(
        total=total,
        active=total - completed,
        completed=completed,
        overdue=overdue,
        due_today=due_today,
        completion_rate=round(completed / total * 100, 1) if total else 0.0,
        by_priority=by_priority,
        by_category=by_category,
    )


@router.delete("/completed", response_model=ClearCompletedResponse)
def clear_completed(db: Session = Depends(get_db)):
    """Delete every completed todo."""
    result = db.execute(delete(Todo).where(Todo.completed.is_(True)))
    db.commit()
    return ClearCompletedResponse(deleted=result.rowcount or 0)


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, todo_id)


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo(**payload.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    """Update any subset of fields; description and due_date may be cleared with null."""
    todo = _get_or_404(db, todo_id)
    changes = payload.model_dump(exclude_unset=True)

    for field in ("title", "category", "priority", "completed"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=422, detail=f"'{field}' cannot be null")

    if "completed" in changes:
        _set_completed(todo, changes.pop("completed"))
    for field, value in changes.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/{todo_id}/toggle", response_model=TodoResponse)
def toggle_todo(todo_id: int, db: Session = Depends(get_db)):
    """Flip a todo between active and completed."""
    todo = _get_or_404(db, todo_id)
    _set_completed(todo, not todo.completed)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = _get_or_404(db, todo_id)
    db.delete(todo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
