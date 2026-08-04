from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    life_area_id: Mapped[int | None] = mapped_column(
        ForeignKey("life_areas.id"),
        nullable=True,
        index=True,
    )

    goal_id: Mapped[int | None] = mapped_column(
        ForeignKey("goals.id"),
        nullable=True,
        index=True,
    )

    habit_id: Mapped[int | None] = mapped_column(
        ForeignKey("habits.id"),
        nullable=True,
        index=True,
    )

    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    session_type: Mapped[str] = mapped_column(
        String(30),
        default="focus",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="running",
        nullable=False,
        index=True,
    )

    planned_duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    accumulated_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    last_resumed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )