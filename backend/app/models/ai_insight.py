from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AiInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    related_goal_id: Mapped[int | None] = mapped_column(
        ForeignKey("goals.id"),
        nullable=True,
        index=True,
    )

    insight_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    insight_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), default="rule_based", nullable=False)

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(String(3000), nullable=False)
    recommendation: Mapped[str | None] = mapped_column(String(1500), nullable=True)

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