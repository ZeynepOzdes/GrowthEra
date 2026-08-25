from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.goal import Goal
from app.models.habit import Habit, HabitLog
from app.models.life_area import LifeArea, UserArea
from app.models.user import User
from app.schemas.habit import (
    HabitCreate,
    HabitLogCreate,
    HabitLogResponse,
    HabitResponse,
    HabitStatus,
    HabitUpdate,
)
from app.services.garden_service import update_habit_tree_from_habit
from app.services.garden_v2_service import update_habit_tree_state_from_habit


router = APIRouter(
    prefix="/habits",
    tags=["Habits"],
)


def get_user_habit_or_404(habit_id: int, user_id: int, db: Session) -> Habit:
    habit = (
        db.query(Habit)
        .filter(
            Habit.id == habit_id,
            Habit.user_id == user_id,
        )
        .first()
    )

    if habit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found.",
        )

    return habit


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
            detail="You must select this life area before creating a habit.",
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
            detail="Cannot attach a habit to an archived goal.",
        )


def sync_goal_progress_from_habit_logs(
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

    if goal.target_unit is None:
        return

    total_value = (
        db.query(func.coalesce(func.sum(HabitLog.value), 0))
        .join(Habit, Habit.id == HabitLog.habit_id)
        .filter(
            Habit.user_id == user_id,
            Habit.goal_id == goal.id,
            Habit.status != "archived",
            Habit.target_unit == goal.target_unit,
            HabitLog.user_id == user_id,
            HabitLog.value.isnot(None),
        )
        .scalar()
    )

    goal.current_value = float(total_value or 0)

    if goal.target_value is not None and goal.target_value > 0:
        if goal.current_value >= goal.target_value:
            goal.status = "completed"
        elif goal.status == "completed":
            goal.status = "active"


def sync_habit_garden_layers(
    habit: Habit,
    user: User,
    db: Session,
) -> None:
    update_habit_tree_from_habit(
        habit=habit,
        db=db,
    )

    update_habit_tree_state_from_habit(
        habit=habit,
        user=user,
        db=db,
    )


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(
    habit_data: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ensure_life_area_is_selected(
        life_area_id=habit_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    ensure_goal_belongs_to_user(
        goal_id=habit_data.goal_id,
        life_area_id=habit_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    habit = Habit(
        user_id=current_user.id,
        life_area_id=habit_data.life_area_id,
        goal_id=habit_data.goal_id,
        title=habit_data.title,
        description=habit_data.description,
        frequency=habit_data.frequency,
        target_value=habit_data.target_value,
        target_unit=habit_data.target_unit,
        status="active",
    )

    db.add(habit)
    db.commit()
    db.refresh(habit)

    return habit


@router.get("/", response_model=list[HabitResponse])
def get_habits(
    status_filter: HabitStatus | None = Query(default=None, alias="status"),
    life_area_id: int | None = None,
    goal_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Habit).filter(Habit.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(Habit.status == status_filter)

    if life_area_id is not None:
        query = query.filter(Habit.life_area_id == life_area_id)

    if goal_id is not None:
        query = query.filter(Habit.goal_id == goal_id)

    habits = query.order_by(Habit.created_at.desc()).all()

    return habits


@router.get("/{habit_id}", response_model=HabitResponse)
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    return habit


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    update_data = habit_data.model_dump(exclude_unset=True)

    new_life_area_id = update_data.get("life_area_id", habit.life_area_id)
    new_goal_id = update_data.get("goal_id", habit.goal_id)

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

    for field, value in update_data.items():
        setattr(habit, field, value)

    sync_habit_garden_layers(
        habit=habit,
        user=current_user,
        db=db,
    )

    db.commit()
    db.refresh(habit)

    return habit


@router.post("/{habit_id}/logs", response_model=HabitLogResponse, status_code=status.HTTP_201_CREATED)
def log_habit(
    habit_id: int,
    log_data: HabitLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    if habit.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active habits can be logged.",
        )

    completed_status = log_data.is_completed

    if habit.target_value is not None:
        if log_data.value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A value is required for habits with a target value.",
            )

        completed_status = log_data.value >= habit.target_value

    existing_log = (
        db.query(HabitLog)
        .filter(
            HabitLog.habit_id == habit.id,
            HabitLog.user_id == current_user.id,
            HabitLog.log_date == log_data.log_date,
        )
        .first()
    )

    if existing_log:
        existing_log.value = log_data.value
        existing_log.is_completed = completed_status
        existing_log.note = log_data.note

        db.flush()

        sync_goal_progress_from_habit_logs(
            goal_id=habit.goal_id,
            user_id=current_user.id,
            db=db,
        )

        sync_habit_garden_layers(
            habit=habit,
            user=current_user,
            db=db,
        )

        db.commit()
        db.refresh(existing_log)

        return existing_log

    habit_log = HabitLog(
        habit_id=habit.id,
        user_id=current_user.id,
        log_date=log_data.log_date,
        value=log_data.value,
        is_completed=completed_status,
        note=log_data.note,
    )

    db.add(habit_log)
    db.flush()

    sync_goal_progress_from_habit_logs(
        goal_id=habit.goal_id,
        user_id=current_user.id,
        db=db,
    )

    sync_habit_garden_layers(
        habit=habit,
        user=current_user,
        db=db,
    )

    db.commit()
    db.refresh(habit_log)

    return habit_log


@router.get("/{habit_id}/logs", response_model=list[HabitLogResponse])
def get_habit_logs(
    habit_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    query = (
        db.query(HabitLog)
        .filter(
            HabitLog.habit_id == habit.id,
            HabitLog.user_id == current_user.id,
        )
    )

    if start_date is not None:
        query = query.filter(HabitLog.log_date >= start_date)

    if end_date is not None:
        query = query.filter(HabitLog.log_date <= end_date)

    logs = query.order_by(HabitLog.log_date.desc()).all()

    return logs


@router.patch("/{habit_id}/pause", response_model=HabitResponse)
def pause_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    habit.status = "paused"

    sync_habit_garden_layers(
        habit=habit,
        user=current_user,
        db=db,
    )

    db.commit()
    db.refresh(habit)

    return habit


@router.patch("/{habit_id}/reactivate", response_model=HabitResponse)
def reactivate_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    habit.status = "active"

    sync_habit_garden_layers(
        habit=habit,
        user=current_user,
        db=db,
    )

    db.commit()
    db.refresh(habit)

    return habit


@router.delete("/{habit_id}")
def archive_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    habit = get_user_habit_or_404(
        habit_id=habit_id,
        user_id=current_user.id,
        db=db,
    )

    habit.status = "archived"

    sync_habit_garden_layers(
        habit=habit,
        user=current_user,
        db=db,
    )

    db.commit()

    return {
        "message": "Habit archived successfully.",
    }