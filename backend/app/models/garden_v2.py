from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class GardenPlot(Base):
    __tablename__ = "garden_plots"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "plot_index",
            name="uq_garden_plot_user_plot_index",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    plot_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    start_journey_day: Mapped[int] = mapped_column(Integer, nullable=False)
    end_journey_day: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    rows: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    columns: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

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


class GardenObject(Base):
    __tablename__ = "garden_objects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    garden_plot_id: Mapped[int] = mapped_column(
        ForeignKey("garden_plots.id"),
        nullable=False,
        index=True,
    )

    element_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    object_subtype: Mapped[str] = mapped_column(String(80), nullable=False)

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    position_row: Mapped[int] = mapped_column(Integer, nullable=False)
    position_column: Mapped[int] = mapped_column(Integer, nullable=False)

    layer: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    is_persistent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    visible_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    metadata_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)

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


class HabitTreeState(Base):
    __tablename__ = "habit_tree_states"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "habit_id",
            name="uq_habit_tree_state_user_habit",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id"),
        nullable=False,
        index=True,
    )

    growth_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_dormant: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    active_cycle_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

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


class HabitTreeCycle(Base):
    __tablename__ = "habit_tree_cycles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "habit_id",
            "cycle_number",
            name="uq_habit_tree_cycle_user_habit_cycle",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id"),
        nullable=False,
        index=True,
    )

    garden_plot_id: Mapped[int] = mapped_column(
        ForeignKey("garden_plots.id"),
        nullable=False,
        index=True,
    )

    garden_object_id: Mapped[int | None] = mapped_column(
        ForeignKey("garden_objects.id"),
        nullable=True,
        index=True,
    )

    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    cycle_start_growth_point: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle_end_growth_point: Mapped[int] = mapped_column(Integer, nullable=False)

    growth_points_in_cycle: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

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