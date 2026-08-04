from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.daily_checkin import DailyCheckIn
from app.models.goal import Goal
from app.models.habit import Habit, HabitLog
from app.models.life_area import LifeArea, UserArea
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = date.today()

    selected_life_areas = (
        db.query(LifeArea)
        .join(UserArea, UserArea.life_area_id == LifeArea.id)
        .filter(
            UserArea.user_id == current_user.id,
            UserArea.is_active == True,
        )
        .order_by(LifeArea.name.asc())
        .all()
    )

    active_goals = (
        db.query(Goal)
        .filter(
            Goal.user_id == current_user.id,
            Goal.status == "active",
        )
        .order_by(Goal.created_at.desc())
        .all()
    )

    completed_goals_count = (
        db.query(Goal)
        .filter(
            Goal.user_id == current_user.id,
            Goal.status == "completed",
        )
        .count()
    )

    progress_values = [
        goal.progress_percentage
        for goal in active_goals
        if goal.progress_percentage is not None
    ]

    average_active_goal_progress = (
        round(sum(progress_values) / len(progress_values), 2)
        if progress_values
        else None
    )

    active_habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == current_user.id,
            Habit.status == "active",
        )
        .order_by(Habit.created_at.desc())
        .all()
    )

    active_habit_ids = [habit.id for habit in active_habits]

    today_logs: list[HabitLog] = []

    if active_habit_ids:
        today_logs = (
            db.query(HabitLog)
            .filter(
                HabitLog.user_id == current_user.id,
                HabitLog.habit_id.in_(active_habit_ids),
                HabitLog.log_date == today,
            )
            .all()
        )

    logs_by_habit_id = {
        habit_log.habit_id: habit_log
        for habit_log in today_logs
    }

    completed_habits_today = sum(
        1
        for habit_log in today_logs
        if habit_log.is_completed
    )

    active_habits_count = len(active_habits)

    habit_completion_rate_today = (
        round((completed_habits_today / active_habits_count) * 100, 2)
        if active_habits_count > 0
        else None
    )

    today_habits = []

    for habit in active_habits:
        today_log = logs_by_habit_id.get(habit.id)

        today_habits.append(
            {
                "id": habit.id,
                "life_area_id": habit.life_area_id,
                "goal_id": habit.goal_id,
                "title": habit.title,
                "frequency": habit.frequency,
                "target_value": habit.target_value,
                "target_unit": habit.target_unit,
                "completed_today": bool(today_log and today_log.is_completed),
                "today_value": today_log.value if today_log else None,
            }
        )

    today_checkin = (
        db.query(DailyCheckIn)
        .filter(
            DailyCheckIn.user_id == current_user.id,
            DailyCheckIn.checkin_date == today,
        )
        .first()
    )

    recent_checkins = (
        db.query(DailyCheckIn)
        .filter(DailyCheckIn.user_id == current_user.id)
        .order_by(DailyCheckIn.checkin_date.desc())
        .limit(7)
        .all()
    )

    return {
        "summary_date": today,
        "user_id": current_user.id,
        "selected_life_areas_count": len(selected_life_areas),
        "active_goals_count": len(active_goals),
        "completed_goals_count": completed_goals_count,
        "average_active_goal_progress": average_active_goal_progress,
        "active_habits_count": active_habits_count,
        "completed_habits_today": completed_habits_today,
        "habit_completion_rate_today": habit_completion_rate_today,
        "today_checkin_completed": today_checkin is not None,
        "selected_life_areas": selected_life_areas,
        "top_active_goals": active_goals[:5],
        "today_habits": today_habits,
        "today_checkin": today_checkin,
        "recent_checkins": recent_checkins,
    }