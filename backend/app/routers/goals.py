from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.goal import Goal
from app.models.life_area import LifeArea, UserArea
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalProgressUpdate, GoalResponse, GoalStatus, GoalUpdate


router = APIRouter(
    prefix="/goals",
    tags=["Goals"],
)


def get_user_goal_or_404(goal_id: int, user_id: int, db: Session) -> Goal:
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

    return goal


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
            detail="You must select this life area before creating a goal.",
        )


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ensure_life_area_is_selected(
        life_area_id=goal_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    goal = Goal(
        user_id=current_user.id,
        life_area_id=goal_data.life_area_id,
        title=goal_data.title,
        description=goal_data.description,
        goal_type=goal_data.goal_type,
        target_value=goal_data.target_value,
        target_unit=goal_data.target_unit,
        start_date=goal_data.start_date,
        end_date=goal_data.end_date,
        priority=goal_data.priority,
        difficulty=goal_data.difficulty,
        status="active",
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@router.get("/", response_model=list[GoalResponse])
def get_goals(
    status_filter: GoalStatus | None = Query(default=None, alias="status"),
    life_area_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Goal).filter(Goal.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(Goal.status == status_filter)

    if life_area_id is not None:
        query = query.filter(Goal.life_area_id == life_area_id)

    goals = query.order_by(Goal.created_at.desc()).all()

    return goals


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    update_data = goal_data.model_dump(exclude_unset=True)

    if "life_area_id" in update_data:
        ensure_life_area_is_selected(
            life_area_id=update_data["life_area_id"],
            user_id=current_user.id,
            db=db,
        )

    for field, value in update_data.items():
        setattr(goal, field, value)

    db.commit()
    db.refresh(goal)

    return goal


@router.patch("/{goal_id}/progress", response_model=GoalResponse)
def update_goal_progress(
    goal_id: int,
    progress_data: GoalProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    goal.current_value = progress_data.current_value

    if goal.target_value is not None and goal.target_value > 0:
        if goal.current_value >= goal.target_value:
            goal.status = "completed"

    db.commit()
    db.refresh(goal)

    return goal


@router.patch("/{goal_id}/complete", response_model=GoalResponse)
def complete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    goal.status = "completed"

    if goal.target_value is not None:
        goal.current_value = goal.target_value

    db.commit()
    db.refresh(goal)

    return goal


@router.patch("/{goal_id}/pause", response_model=GoalResponse)
def pause_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    goal.status = "paused"

    db.commit()
    db.refresh(goal)

    return goal


@router.patch("/{goal_id}/reactivate", response_model=GoalResponse)
def reactivate_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    goal.status = "active"

    db.commit()
    db.refresh(goal)

    return goal


@router.delete("/{goal_id}")
def archive_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    goal = get_user_goal_or_404(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
    )

    goal.status = "archived"

    db.commit()

    return {
        "message": "Goal archived successfully.",
    }