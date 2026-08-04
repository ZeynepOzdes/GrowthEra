from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.ai_insight import AiInsight
from app.models.daily_checkin import DailyCheckIn
from app.models.goal import Goal
from app.models.habit import Habit, HabitLog
from app.models.user import User
from app.schemas.ai import AiInsightResponse, AiInsightStatusUpdate


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


def build_rule_based_daily_review(
    db: Session,
    user_id: int,
    review_date: date,
) -> tuple[str, str, str | None]:
    active_goals = (
        db.query(Goal)
        .filter(
            Goal.user_id == user_id,
            Goal.status == "active",
        )
        .all()
    )

    active_habits = (
        db.query(Habit)
        .filter(
            Habit.user_id == user_id,
            Habit.status == "active",
        )
        .all()
    )

    active_habit_ids = [habit.id for habit in active_habits]

    today_logs: list[HabitLog] = []

    if active_habit_ids:
        today_logs = (
            db.query(HabitLog)
            .filter(
                HabitLog.user_id == user_id,
                HabitLog.habit_id.in_(active_habit_ids),
                HabitLog.log_date == review_date,
            )
            .all()
        )

    completed_habits_count = sum(
        1 for habit_log in today_logs if habit_log.is_completed
    )

    active_habits_count = len(active_habits)

    habit_completion_rate = (
        round((completed_habits_count / active_habits_count) * 100, 2)
        if active_habits_count > 0
        else None
    )

    today_checkin = (
        db.query(DailyCheckIn)
        .filter(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.checkin_date == review_date,
        )
        .first()
    )

    title = "Daily growth review"

    content_parts: list[str] = []
    recommendation_parts: list[str] = []

    if not active_goals:
        content_parts.append(
            "You do not have any active goals yet. Growth becomes easier when your direction is clear."
        )
        recommendation_parts.append(
            "Create one realistic goal connected to a life area you want to improve."
        )
    else:
        content_parts.append(
            f"You currently have {len(active_goals)} active goal(s)."
        )

    if active_habits_count == 0:
        content_parts.append(
            "You do not have any active habits yet. Goals are easier to follow when they are connected to small repeatable actions."
        )
        recommendation_parts.append(
            "Create one simple habit that supports your most important goal."
        )
    else:
        content_parts.append(
            f"Today, you completed {completed_habits_count} out of {active_habits_count} active habit(s)."
        )

        if habit_completion_rate is not None:
            if habit_completion_rate >= 80:
                content_parts.append(
                    "Your habit completion rate is strong today. This is a good sign of consistency."
                )
                recommendation_parts.append(
                    "Keep the same rhythm tomorrow instead of increasing the difficulty too quickly."
                )
            elif habit_completion_rate >= 40:
                content_parts.append(
                    "You made partial progress today. This still matters because consistency is built through repeated attempts."
                )
                recommendation_parts.append(
                    "Focus on completing one more small habit before the day ends, if possible."
                )
            else:
                content_parts.append(
                    "Your habit completion rate is low today. This may mean the plan is too heavy or your energy is limited."
                )
                recommendation_parts.append(
                    "Choose the smallest useful action and complete only that. Protect consistency before intensity."
                )

    if today_checkin is None:
        content_parts.append(
            "You have not completed today's check-in yet, so the system has limited context about your mood, energy, focus, stress, and sleep."
        )
        recommendation_parts.append(
            "Complete your daily check-in to make future insights more personalized."
        )
    else:
        if today_checkin.energy_score is not None and today_checkin.energy_score <= 4:
            content_parts.append(
                "Your energy score is low today, so pushing too hard may not be the best strategy."
            )
            recommendation_parts.append(
                "Use a smaller target today and aim for a short focused session."
            )

        if today_checkin.sleep_quality_score is not None and today_checkin.sleep_quality_score <= 4:
            content_parts.append(
                "Your sleep quality score is low. This can affect focus and habit completion."
            )
            recommendation_parts.append(
                "Avoid increasing your workload tomorrow unless your energy improves."
            )

        if today_checkin.focus_score is not None and today_checkin.focus_score >= 7:
            content_parts.append(
                "Your focus score is relatively strong today."
            )
            recommendation_parts.append(
                "Use this focus window for your most important goal-related task."
            )

        if today_checkin.stress_score is not None and today_checkin.stress_score >= 8:
            content_parts.append(
                "Your stress score is high today. A strict plan may feel harder to follow."
            )
            recommendation_parts.append(
                "Break your next task into a smaller step and avoid judging the whole day from one difficult period."
            )

    content = " ".join(content_parts)
    recommendation = " ".join(recommendation_parts) if recommendation_parts else None

    return title, content, recommendation


@router.post("/daily-review", response_model=AiInsightResponse, status_code=status.HTTP_201_CREATED)
def create_daily_review(
    review_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    target_date = review_date or date.today()

    title, content, recommendation = build_rule_based_daily_review(
        db=db,
        user_id=current_user.id,
        review_date=target_date,
    )

    existing_insight = (
        db.query(AiInsight)
        .filter(
            AiInsight.user_id == current_user.id,
            AiInsight.insight_type == "daily_review",
            AiInsight.insight_date == target_date,
            AiInsight.status != "archived",
        )
        .first()
    )

    if existing_insight:
        existing_insight.title = title
        existing_insight.content = content
        existing_insight.recommendation = recommendation
        existing_insight.source = "rule_based"
        existing_insight.status = "active"

        db.commit()
        db.refresh(existing_insight)

        return existing_insight

    insight = AiInsight(
        user_id=current_user.id,
        related_goal_id=None,
        insight_date=target_date,
        insight_type="daily_review",
        source="rule_based",
        title=title,
        content=content,
        recommendation=recommendation,
        status="active",
    )

    db.add(insight)
    db.commit()
    db.refresh(insight)

    return insight


@router.get("/insights", response_model=list[AiInsightResponse])
def get_ai_insights(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(AiInsight).filter(AiInsight.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(AiInsight.status == status_filter)

    insights = (
        query
        .order_by(AiInsight.created_at.desc())
        .limit(limit)
        .all()
    )

    return insights


@router.patch("/insights/{insight_id}/status", response_model=AiInsightResponse)
def update_ai_insight_status(
    insight_id: int,
    status_data: AiInsightStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    insight = (
        db.query(AiInsight)
        .filter(
            AiInsight.id == insight_id,
            AiInsight.user_id == current_user.id,
        )
        .first()
    )

    if insight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI insight not found.",
        )

    insight.status = status_data.status

    db.commit()
    db.refresh(insight)

    return insight