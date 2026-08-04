from datetime import date

from pydantic import BaseModel, ConfigDict


class DashboardLifeAreaSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    icon: str | None


class DashboardGoalSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    life_area_id: int

    title: str
    goal_type: str

    target_value: float | None
    target_unit: str | None
    current_value: float
    progress_percentage: float | None

    priority: str
    status: str
    end_date: date | None


class DashboardHabitTodaySummary(BaseModel):
    id: int
    life_area_id: int
    goal_id: int | None

    title: str
    frequency: str

    target_value: float | None
    target_unit: str | None

    completed_today: bool
    today_value: float | None


class DashboardCheckInSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checkin_date: date

    mood_score: int | None
    energy_score: int | None
    focus_score: int | None
    stress_score: int | None
    sleep_quality_score: int | None

    note: str | None


class DashboardSummaryResponse(BaseModel):
    summary_date: date
    user_id: int

    selected_life_areas_count: int

    active_goals_count: int
    completed_goals_count: int
    average_active_goal_progress: float | None

    active_habits_count: int
    completed_habits_today: int
    habit_completion_rate_today: float | None

    today_checkin_completed: bool

    selected_life_areas: list[DashboardLifeAreaSummary]
    top_active_goals: list[DashboardGoalSummary]
    today_habits: list[DashboardHabitTodaySummary]

    today_checkin: DashboardCheckInSummary | None
    recent_checkins: list[DashboardCheckInSummary]