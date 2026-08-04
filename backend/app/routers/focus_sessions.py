from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.focus_session import FocusSession
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.life_area import LifeArea, UserArea
from app.models.task import Task
from app.models.user import User
from app.schemas.focus_session import (
    FocusDashboardSummaryResponse,
    FocusSessionCreate,
    FocusSessionResponse,
    FocusTaskSummaryResponse,
)


router = APIRouter(
    prefix="/focus-sessions",
    tags=["Focus Sessions"],
)


def calculate_session_seconds(session: FocusSession, now: datetime | None = None) -> int:
    current_time = now or datetime.utcnow()

    total_seconds = session.accumulated_seconds or 0

    if session.status == "running" and session.last_resumed_at is not None:
        interval_seconds = int(
            (current_time - session.last_resumed_at).total_seconds()
        )
        total_seconds += max(interval_seconds, 0)

    return total_seconds


def get_user_focus_session_or_404(
    session_id: int,
    user_id: int,
    db: Session,
) -> FocusSession:
    session = (
        db.query(FocusSession)
        .filter(
            FocusSession.id == session_id,
            FocusSession.user_id == user_id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Focus session not found.",
        )

    return session


def validate_life_area_access(
    life_area_id: int | None,
    user_id: int,
    db: Session,
) -> None:
    if life_area_id is None:
        return

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
            detail="You can only start focus sessions for selected life areas.",
        )


def validate_goal_access(
    goal_id: int | None,
    user_id: int,
    db: Session,
) -> Goal | None:
    if goal_id is None:
        return None

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

    if goal.status in ["completed", "archived"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed or archived goals cannot be used for new focus sessions.",
        )

    return goal


def validate_habit_access(
    habit_id: int | None,
    user_id: int,
    db: Session,
) -> Habit | None:
    if habit_id is None:
        return None

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

    if habit.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archived habits cannot be used for new focus sessions.",
        )

    return habit


def validate_task_access(
    task_id: int | None,
    user_id: int,
    db: Session,
) -> Task | None:
    if task_id is None:
        return None

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

    if task.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archived tasks cannot be used for new focus sessions.",
        )

    if task.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed tasks cannot be used for new focus sessions.",
        )

    return task


@router.post("/start", response_model=FocusSessionResponse)
def start_focus_session(
    session_data: FocusSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    existing_active_session = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.status.in_(["running", "paused"]),
        )
        .first()
    )

    if existing_active_session is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active focus session.",
        )

    task = validate_task_access(
        task_id=session_data.task_id,
        user_id=current_user.id,
        db=db,
    )

    validate_goal_access(
        goal_id=session_data.goal_id,
        user_id=current_user.id,
        db=db,
    )

    validate_habit_access(
        habit_id=session_data.habit_id,
        user_id=current_user.id,
        db=db,
    )

    validate_life_area_access(
        life_area_id=session_data.life_area_id,
        user_id=current_user.id,
        db=db,
    )

    if task is not None and task.status == "active":
        task.status = "ongoing"
        task.updated_at = datetime.utcnow()

    now = datetime.utcnow()

    focus_session = FocusSession(
        user_id=current_user.id,
        life_area_id=session_data.life_area_id,
        goal_id=session_data.goal_id,
        habit_id=session_data.habit_id,
        task_id=session_data.task_id,
        title=session_data.title,
        session_type=session_data.session_type,
        status="running",
        planned_duration_minutes=session_data.planned_duration_minutes,
        accumulated_seconds=0,
        duration_seconds=None,
        started_at=now,
        last_resumed_at=now,
        paused_at=None,
        ended_at=None,
        note=session_data.note,
        created_at=now,
        updated_at=now,
    )

    db.add(focus_session)
    db.commit()
    db.refresh(focus_session)

    return focus_session


@router.get("/active", response_model=FocusSessionResponse | None)
def get_active_focus_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    active_session = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.status.in_(["running", "paused"]),
        )
        .order_by(FocusSession.started_at.desc())
        .first()
    )

    return active_session


@router.get("/task-summary", response_model=list[FocusTaskSummaryResponse])
def get_task_focus_summary(
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tasks_query = db.query(Task).filter(Task.user_id == current_user.id)

    if not include_archived:
        tasks_query = tasks_query.filter(Task.status != "archived")

    user_tasks = tasks_query.order_by(Task.created_at.desc()).all()

    completed_rows = (
        db.query(
            FocusSession.task_id.label("task_id"),
            func.coalesce(func.sum(FocusSession.duration_seconds), 0).label(
                "total_focus_seconds"
            ),
            func.count(FocusSession.id).label("completed_sessions_count"),
            func.max(FocusSession.ended_at).label("last_session_at"),
        )
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.task_id.isnot(None),
            FocusSession.status == "completed",
        )
        .group_by(FocusSession.task_id)
        .all()
    )

    completed_summary_by_task_id = {
        row.task_id: {
            "total_focus_seconds": int(row.total_focus_seconds or 0),
            "completed_sessions_count": int(row.completed_sessions_count or 0),
            "last_session_at": row.last_session_at,
        }
        for row in completed_rows
    }

    active_sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.task_id.isnot(None),
            FocusSession.status.in_(["running", "paused"]),
        )
        .all()
    )

    active_session_by_task_id = {
        session.task_id: session for session in active_sessions
    }

    now = datetime.utcnow()
    response: list[FocusTaskSummaryResponse] = []

    for task in user_tasks:
        completed_summary = completed_summary_by_task_id.get(
            task.id,
            {
                "total_focus_seconds": 0,
                "completed_sessions_count": 0,
                "last_session_at": None,
            },
        )

        active_session = active_session_by_task_id.get(task.id)

        active_session_seconds = (
            calculate_session_seconds(active_session, now)
            if active_session is not None
            else 0
        )

        total_focus_seconds = completed_summary["total_focus_seconds"]
        total_with_active_seconds = total_focus_seconds + active_session_seconds

        planned_seconds = (
            task.planned_duration_minutes * 60
            if task.planned_duration_minutes is not None
            else None
        )

        progress_percentage = None
        is_over_planned = False

        if planned_seconds is not None and planned_seconds > 0:
            progress_percentage = round(
                (total_with_active_seconds / planned_seconds) * 100,
                2,
            )
            is_over_planned = total_with_active_seconds > planned_seconds

        response.append(
            FocusTaskSummaryResponse(
                task_id=task.id,
                task_title=task.title,
                task_status=task.status,
                planned_duration_minutes=task.planned_duration_minutes,
                total_focus_seconds=total_focus_seconds,
                total_focus_minutes=round(total_focus_seconds / 60, 2),
                completed_sessions_count=completed_summary[
                    "completed_sessions_count"
                ],
                last_session_at=completed_summary["last_session_at"],
                has_active_session=active_session is not None,
                active_session_id=active_session.id if active_session else None,
                active_session_status=active_session.status if active_session else None,
                active_session_seconds=active_session_seconds,
                progress_percentage=progress_percentage,
                is_over_planned=is_over_planned,
            )
        )

    return response


@router.get("/dashboard-summary", response_model=FocusDashboardSummaryResponse)
def get_focus_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    now = datetime.utcnow()

    today_start = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
    )

    tomorrow_start = today_start + timedelta(days=1)

    today_completed_sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.status == "completed",
            FocusSession.ended_at >= today_start,
            FocusSession.ended_at < tomorrow_start,
        )
        .all()
    )

    all_completed_sessions = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.status == "completed",
        )
        .all()
    )

    today_focus_seconds = sum(
        session.duration_seconds or 0 for session in today_completed_sessions
    )

    total_focus_seconds = sum(
        session.duration_seconds or 0 for session in all_completed_sessions
    )

    active_session = (
        db.query(FocusSession)
        .filter(
            FocusSession.user_id == current_user.id,
            FocusSession.status.in_(["running", "paused"]),
        )
        .order_by(FocusSession.started_at.desc())
        .first()
    )

    active_session_seconds = (
        calculate_session_seconds(active_session, now)
        if active_session is not None
        else 0
    )

    return FocusDashboardSummaryResponse(
        today_focus_seconds=today_focus_seconds,
        today_focus_minutes=round(today_focus_seconds / 60, 2),
        completed_sessions_today=len(today_completed_sessions),
        total_focus_seconds=total_focus_seconds,
        total_focus_minutes=round(total_focus_seconds / 60, 2),
        completed_sessions_total=len(all_completed_sessions),
        has_active_session=active_session is not None,
        active_session_id=active_session.id if active_session else None,
        active_session_title=active_session.title if active_session else None,
        active_session_status=active_session.status if active_session else None,
        active_session_task_id=active_session.task_id if active_session else None,
        active_session_seconds=active_session_seconds,
    )


@router.get("/", response_model=list[FocusSessionResponse])
def get_focus_sessions(
    status_filter: str | None = Query(default=None, alias="status"),
    task_id: int | None = None,
    habit_id: int | None = None,
    goal_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id
    )

    if status_filter is not None:
        query = query.filter(FocusSession.status == status_filter)

    if task_id is not None:
        query = query.filter(FocusSession.task_id == task_id)

    if habit_id is not None:
        query = query.filter(FocusSession.habit_id == habit_id)

    if goal_id is not None:
        query = query.filter(FocusSession.goal_id == goal_id)

    return query.order_by(FocusSession.started_at.desc()).limit(limit).all()


@router.patch("/{session_id}/pause", response_model=FocusSessionResponse)
def pause_focus_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = get_user_focus_session_or_404(
        session_id=session_id,
        user_id=current_user.id,
        db=db,
    )

    if session.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only running focus sessions can be paused.",
        )

    now = datetime.utcnow()

    session.accumulated_seconds = calculate_session_seconds(session, now)
    session.status = "paused"
    session.paused_at = now
    session.last_resumed_at = None
    session.updated_at = now

    db.commit()
    db.refresh(session)

    return session


@router.patch("/{session_id}/resume", response_model=FocusSessionResponse)
def resume_focus_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = get_user_focus_session_or_404(
        session_id=session_id,
        user_id=current_user.id,
        db=db,
    )

    if session.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only paused focus sessions can be resumed.",
        )

    now = datetime.utcnow()

    session.status = "running"
    session.last_resumed_at = now
    session.paused_at = None
    session.updated_at = now

    db.commit()
    db.refresh(session)

    return session


@router.patch("/{session_id}/complete", response_model=FocusSessionResponse)
def complete_focus_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = get_user_focus_session_or_404(
        session_id=session_id,
        user_id=current_user.id,
        db=db,
    )

    if session.status not in ["running", "paused"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only running or paused focus sessions can be completed.",
        )

    now = datetime.utcnow()
    final_seconds = calculate_session_seconds(session, now)

    session.status = "completed"
    session.accumulated_seconds = final_seconds
    session.duration_seconds = final_seconds
    session.ended_at = now
    session.last_resumed_at = None
    session.paused_at = None
    session.updated_at = now

    db.commit()
    db.refresh(session)

    return session


@router.patch("/{session_id}/cancel", response_model=FocusSessionResponse)
def cancel_focus_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = get_user_focus_session_or_404(
        session_id=session_id,
        user_id=current_user.id,
        db=db,
    )

    if session.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed or cancelled focus sessions cannot be cancelled.",
        )

    now = datetime.utcnow()
    final_seconds = calculate_session_seconds(session, now)

    session.status = "cancelled"
    session.accumulated_seconds = final_seconds
    session.duration_seconds = None
    session.ended_at = now
    session.last_resumed_at = None
    session.paused_at = None
    session.updated_at = now

    db.commit()
    db.refresh(session)

    return session