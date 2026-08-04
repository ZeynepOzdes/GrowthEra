from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TaskElementType = Literal["earth", "water", "air"]
TaskUrgencyState = Literal["normal", "fire"]
TaskShape = Literal["flower", "rock"]
TaskPriority = Literal["low", "medium", "high"]
TaskStatus = Literal["active", "ongoing", "completed", "paused", "archived"]


class TaskCreate(BaseModel):
    life_area_id: int
    goal_id: int | None = None

    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    element_type: TaskElementType = "earth"
    urgency_state: TaskUrgencyState = "normal"
    task_shape: TaskShape | None = None

    planned_date: date | None = None
    due_date: date | None = None

    planned_duration_minutes: int | None = Field(default=None, ge=1, le=1440)

    priority: TaskPriority = "medium"

    @model_validator(mode="after")
    def validate_task_rules(self):
        today = date.today()

        if self.planned_date is not None and self.planned_date < today:
            raise ValueError("Planned date cannot be in the past.")

        if self.due_date is not None and self.due_date < today:
            raise ValueError("Due date cannot be in the past.")

        if (
            self.planned_date is not None
            and self.due_date is not None
            and self.planned_date > self.due_date
        ):
            raise ValueError("Planned date cannot be later than due date.")

        if self.element_type == "earth" and self.due_date is None:
            raise ValueError("Earth tasks require a due date.")

        if self.element_type == "earth" and self.task_shape is None:
            raise ValueError("Earth tasks require a task shape.")

        if self.element_type != "earth" and self.task_shape is not None:
            raise ValueError("Only earth tasks can have a flower or rock shape.")

        if self.urgency_state == "fire" and self.element_type != "earth":
            raise ValueError("Fire urgency can only be used with earth tasks.")

        return self


class TaskUpdate(BaseModel):
    life_area_id: int | None = None
    goal_id: int | None = None

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)

    element_type: TaskElementType | None = None
    urgency_state: TaskUrgencyState | None = None
    task_shape: TaskShape | None = None

    planned_date: date | None = None
    due_date: date | None = None

    planned_duration_minutes: int | None = Field(default=None, ge=1, le=1440)

    priority: TaskPriority | None = None
    status: TaskStatus | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    life_area_id: int
    goal_id: int | None

    title: str
    description: str | None

    element_type: str
    urgency_state: str
    task_shape: str | None

    planned_date: date | None
    due_date: date | None

    planned_duration_minutes: int | None

    priority: str
    status: str

    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime