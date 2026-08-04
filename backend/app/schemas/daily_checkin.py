from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DailyCheckInCreate(BaseModel):
    checkin_date: date = Field(default_factory=date.today)

    mood_score: int | None = Field(default=None, ge=1, le=10)
    energy_score: int | None = Field(default=None, ge=1, le=10)
    focus_score: int | None = Field(default=None, ge=1, le=10)
    stress_score: int | None = Field(default=None, ge=1, le=10)
    sleep_quality_score: int | None = Field(default=None, ge=1, le=10)

    note: str | None = Field(default=None, max_length=1500)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        has_score = any(
            score is not None
            for score in [
                self.mood_score,
                self.energy_score,
                self.focus_score,
                self.stress_score,
                self.sleep_quality_score,
            ]
        )

        has_note = self.note is not None and self.note.strip() != ""

        if not has_score and not has_note:
            raise ValueError("At least one score or note must be provided.")

        return self


class DailyCheckInUpdate(BaseModel):
    mood_score: int | None = Field(default=None, ge=1, le=10)
    energy_score: int | None = Field(default=None, ge=1, le=10)
    focus_score: int | None = Field(default=None, ge=1, le=10)
    stress_score: int | None = Field(default=None, ge=1, le=10)
    sleep_quality_score: int | None = Field(default=None, ge=1, le=10)

    note: str | None = Field(default=None, max_length=1500)


class DailyCheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

    checkin_date: date

    mood_score: int | None
    energy_score: int | None
    focus_score: int | None
    stress_score: int | None
    sleep_quality_score: int | None

    note: str | None

    created_at: datetime
    updated_at: datetime