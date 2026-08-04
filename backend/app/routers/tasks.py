from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.services.garden_service import create_garden_cell_from_task
from app.models.goal import Goal
from app.models.life_area import LifeArea, UserArea
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskElementType,
    TaskResponse,
    TaskShape,
    TaskStatus,
    TaskUpdate,
    TaskUrgencyState,
)


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


def get_user_task_or_404(task_id: int, user_id: int, db: Session) -> Task:
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task


def ensure_life_area_is_selected(life_area_id: int, user_id: int, db: Session) -> None:
    life_area = db.query(LifeArea).filter(LifeArea.id == life_area_id).first()

    if life_area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found.",
        )

    selected_area = (
        db.query(UserArea)
        .filter(
            UserArea.user_id == user_id,
            UserArea.life_area_id == life_area_id,
            UserArea.is_active == True,
        )
        .first()
    )

    if selected_area is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must select this life area before creating a task.",
        )


def ensure_goal_belongs_to_user(
    goal_id: int | None,
    life_area_id: int,
    user_id: int,
    db: Session,
) -> None:
    if goal_id is None:
        return

    goal = (
        db.query(Goal)
        .filter(
            Goal.id == goal_id,
            Goal.user_id == user_id,
        )
        .first()
    )

    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found.",
        )

    if goal.life_area_id != life_area_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal does not belong to the selected life area.",
        )

    if goal.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot attach a task to an archived goal.",
        )


def validate_task_business_rules(
    element_type: str,
    urgency_state: str,
    planned_date,
    due_date,
    task_shape: str | None,
) -> None:
    today = datetime.utcnow().date()

    if planned_date is not None and planned_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planned date cannot be in the past.",
        )

    if due_date is not None and due_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be in the past.",
        )

    if planned_date is not None and due_date is not None and planned_date > due_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planned date cannot be later than due date.",
        )

    if element_type == "earth" and due_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Earth tasks require a due date.",
        )

    if element_type == "earth" and task_shape is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Earth tasks require a task shape.",
        )

    if element_type != "earth" and task_shape is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only earth tasks can have a flower or rock shape.",
        )

    if urgency_state == "fire" and element_type != "earth":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fire urgency can only be used with earth tasks.",
        )


def sync_goal_progress_from_tasks(
    goal_id: int | None,
    user_id: int,
    db: Session,
) -> None:
    if goal_id is None:
        return

    goal = (
        db.query(Goal)
        .filter(
            Goal.id == goal_id,
            Goal.user_id == user_id,
        )
        .first()
    )

    if goal is None:
        return

    if goal.target_unit not in ["tasks", "completed_tasks"]:
        return

    completed_tasks_count = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.goal_id == goal.id,
            Task.status == "completed",
        )
        .count()
    )

    goal.current_value = float(completed_tasks_count)

    if goal.target_value is not None and goal.target_value > 0:
        if goal.current_value >= goal.target_value:
            goal.status = "completed"
        elif goal.status == "completed":
            goal.status = "active"


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ensure_life_area_is_selected(
        life_area_id=task_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    ensure_goal_belongs_to_user(
        goal_id=task_data.goal_id,
        life_area_id=task_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    clean_task_shape = (
        task_data.task_shape
        if task_data.element_type == "earth"
        else None
    )

    task = Task(
        user_id=current_user.id,
        life_area_id=task_data.life_area_id,
        goal_id=task_data.goal_id,
        title=task_data.title,
        description=task_data.description,
        element_type=task_data.element_type,
        urgency_state=task_data.urgency_state,
        task_shape=clean_task_shape,
        planned_date=task_data.planned_date,
        due_date=task_data.due_date,
        planned_duration_minutes=task_data.planned_duration_minutes,
        priority=task_data.priority,
        status="active",
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    element_type: TaskElementType | None = None,
    urgency_state: TaskUrgencyState | None = None,
    task_shape: TaskShape | None = None,
    life_area_id: int | None = None,
    goal_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(Task.status == status_filter)

    if element_type is not None:
        query = query.filter(Task.element_type == element_type)

    if urgency_state is not None:
        query = query.filter(Task.urgency_state == urgency_state)

    if task_shape is not None:
        query = query.filter(Task.task_shape == task_shape)

    if life_area_id is not None:
        query = query.filter(Task.life_area_id == life_area_id)

    if goal_id is not None:
        query = query.filter(Task.goal_id == goal_id)

    tasks = (
        query
        .order_by(Task.due_date.asc(), Task.priority.desc(), Task.created_at.desc())
        .all()
    )

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    update_data = task_data.model_dump(exclude_unset=True)

    new_life_area_id = update_data.get("life_area_id", task.life_area_id)
    new_goal_id = update_data.get("goal_id", task.goal_id)

    new_element_type = update_data.get("element_type", task.element_type)
    new_urgency_state = update_data.get("urgency_state", task.urgency_state)
    new_planned_date = update_data.get("planned_date", task.planned_date)
    new_due_date = update_data.get("due_date", task.due_date)
    new_task_shape = update_data.get("task_shape", task.task_shape)

    if new_element_type != "earth":
        new_task_shape = None

    if "life_area_id" in update_data:
        ensure_life_area_is_selected(
            life_area_id=new_life_area_id,
            user_id=current_user.id,
            db=db,
        )

    if "goal_id" in update_data or "life_area_id" in update_data:
        ensure_goal_belongs_to_user(
            goal_id=new_goal_id,
            life_area_id=new_life_area_id,
            user_id=current_user.id,
            db=db,
        )

    validate_task_business_rules(
        element_type=new_element_type,
        urgency_state=new_urgency_state,
        planned_date=new_planned_date,
        due_date=new_due_date,
        task_shape=new_task_shape,
    )

    previous_goal_id = task.goal_id

    for field, value in update_data.items():
        task.task_shape = new_task_shape
        setattr(task, field, value)

    db.flush()

    sync_goal_progress_from_tasks(
        goal_id=previous_goal_id,
        user_id=current_user.id,
        db=db,
    )

    sync_goal_progress_from_tasks(
        goal_id=task.goal_id,
        user_id=current_user.id,
        db=db,
    )

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    if task.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archived tasks cannot be completed.",
        )

    if task.status == "completed":
        return task

    now = datetime.utcnow()

    task.status = "completed"
    task.completed_at = now
    task.updated_at = now

    create_garden_cell_from_task(task=task, db=db)

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/pause", response_model=TaskResponse)
def pause_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    task.status = "paused"

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/reactivate", response_model=TaskResponse)
def reactivate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    task.status = "active"
    task.completed_at = None

    db.flush()

    sync_goal_progress_from_tasks(
        goal_id=task.goal_id,
        user_id=current_user.id,
        db=db,
    )

    db.commit()
    db.refresh(task)

    return task

@router.patch("/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    if task.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archived tasks cannot be started.",
        )

    if task.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed tasks cannot be started.",
        )

    task.status = "ongoing"

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/fire", response_model=TaskResponse)
def mark_task_as_fire(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    if task.element_type != "earth":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only earth tasks can enter fire urgency.",
        )

    task.urgency_state = "fire"

    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/normalize", response_model=TaskResponse)
def normalize_task_urgency(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    task.urgency_state = "normal"

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}")
def archive_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = get_user_task_or_404(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    task.status = "archived"

    db.flush()

    sync_goal_progress_from_tasks(
        goal_id=task.goal_id,
        user_id=current_user.id,
        db=db,
    )

    db.commit()

    return {
        "message": "Task archived successfully.",
    }