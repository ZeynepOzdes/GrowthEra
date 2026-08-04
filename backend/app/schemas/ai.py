from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


AiInsightStatus = Literal["active", "accepted", "rejected", "archived"]


class AiInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    related_goal_id: int | None

    insight_date: date

    insight_type: str
    source: str

    title: str
    content: str
    recommendation: str | None

    status: str

    created_at: datetime
    updated_at: datetime


class AiInsightStatusUpdate(BaseModel):
    status: AiInsightStatus