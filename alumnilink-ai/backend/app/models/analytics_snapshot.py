from datetime import datetime, date
from sqlalchemy import Date, DateTime, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("snapshot_date", name="uq_analytics_snapshots_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
