from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


GoalType = Literal["outcome", "process", "habit", "limit", "project"]
GoalPriority = Literal["low", "medium", "high"]
GoalDifficulty = Literal["easy", "medium", "hard"]
GoalStatus = Literal["active", "completed", "paused", "archived"]


class GoalCreate(BaseModel):
    life_area_id: int
    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    goal_type: GoalType = "outcome"

    target_value: float | None = Field(default=None, ge=0)
    target_unit: str | None = Field(default=None, max_length=50)

    start_date: date | None = None
    end_date: date | None = None

    priority: GoalPriority = "medium"
    difficulty: GoalDifficulty = "medium"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date.")

        return self


class GoalUpdate(BaseModel):
    life_area_id: int | None = None
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    goal_type: GoalType | None = None

    target_value: float | None = Field(default=None, ge=0)
    target_unit: str | None = Field(default=None, max_length=50)
    current_value: float | None = Field(default=None, ge=0)

    start_date: date | None = None
    end_date: date | None = None

    priority: GoalPriority | None = None
    difficulty: GoalDifficulty | None = None
    status: GoalStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date.")

        return self


class GoalProgressUpdate(BaseModel):
    current_value: float = Field(ge=0)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    life_area_id: int

    title: str
    description: str | None

    goal_type: str

    target_value: float | None
    target_unit: str | None
    current_value: float
    progress_percentage: float | None

    start_date: date | None
    end_date: date | None

    priority: str
    difficulty: str
    status: str

    created_at: datetime
    updated_at: datetime