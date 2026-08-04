from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LifeAreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    icon: str | None
    is_default: bool
    created_at: datetime


class UserAreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    life_area_id: int
    is_active: bool
    created_at: datetime


class CustomLifeAreaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    icon: str | None = Field(default=None, max_length=50)