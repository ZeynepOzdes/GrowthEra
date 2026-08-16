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