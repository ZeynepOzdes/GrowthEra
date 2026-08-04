from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


FocusSessionStatus = Literal["running", "paused", "completed", "cancelled"]
FocusSessionType = Literal["focus", "task", "habit", "goal", "general"]


class FocusSessionCreate(BaseModel):
    life_area_id: int | None = None
    goal_id: int | None = None
    habit_id: int | None = None
    task_id: int | None = None

    title: str = Field(min_length=3, max_length=150)
    session_type: FocusSessionType = "focus"

    planned_duration_minutes: int | None = Field(default=None, ge=1, le=1440)

    note: str | None = Field(default=None, max_length=1000)


class FocusSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

    life_area_id: int | None
    goal_id: int | None
    habit_id: int | None
    task_id: int | None

    title: str
    session_type: str
    status: str

    planned_duration_minutes: int | None

    accumulated_seconds: int
    duration_seconds: int | None

    started_at: datetime
    last_resumed_at: datetime | None
    paused_at: datetime | None
    ended_at: datetime | None

    note: str | None

    created_at: datetime
    updated_at: datetime


class FocusTaskSummaryResponse(BaseModel):
    task_id: int
    task_title: str
    task_status: str

    planned_duration_minutes: int | None

    total_focus_seconds: int
    total_focus_minutes: float

    completed_sessions_count: int
    last_session_at: datetime | None

    has_active_session: bool
    active_session_id: int | None
    active_session_status: str | None
    active_session_seconds: int

    progress_percentage: float | None
    is_over_planned: bool


class FocusDashboardSummaryResponse(BaseModel):
    today_focus_seconds: int
    today_focus_minutes: float
    completed_sessions_today: int

    total_focus_seconds: int
    total_focus_minutes: float
    completed_sessions_total: int

    has_active_session: bool
    active_session_id: int | None
    active_session_title: str | None
    active_session_status: str | None
    active_session_task_id: int | None
    active_session_seconds: int