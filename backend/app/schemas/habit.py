from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


HabitFrequency = Literal["daily", "weekly", "custom"]
HabitStatus = Literal["active", "paused", "archived"]


class HabitCreate(BaseModel):
    life_area_id: int
    goal_id: int | None = None

    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    frequency: HabitFrequency = "daily"

    target_value: float | None = Field(default=None, ge=0)
    target_unit: str | None = Field(default=None, max_length=50)


class HabitUpdate(BaseModel):
    life_area_id: int | None = None
    goal_id: int | None = None

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    frequency: HabitFrequency | None = None

    target_value: float | None = Field(default=None, ge=0)
    target_unit: str | None = Field(default=None, max_length=50)

    status: HabitStatus | None = None


class HabitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    life_area_id: int
    goal_id: int | None

    title: str
    description: str | None

    frequency: str

    target_value: float | None
    target_unit: str | None

    status: str

    created_at: datetime
    updated_at: datetime


class HabitLogCreate(BaseModel):
    log_date: date = Field(default_factory=date.today)

    value: float | None = Field(default=None, ge=0)
    is_completed: bool = True

    note: str | None = Field(default=None, max_length=1000)


class HabitLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    user_id: int

    log_date: date
    value: float | None
    is_completed: bool

    note: str | None

    created_at: datetime
    updated_at: datetime