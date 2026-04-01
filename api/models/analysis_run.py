"""AnalysisRun ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

try:
    from sqlalchemy import JSON
    _JSON = JSON
except ImportError:
    from sqlalchemy import Text as _JSON  # type: ignore[assignment]


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="created"
    )  # created | ingested | quality_done | capacity_done | performance_done

    # File paths on persistent disk
    masterdata_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    orders_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB columns (stored as JSON/Text depending on DB)
    masterdata_mapping: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    orders_mapping: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    quality_result: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    capacity_result: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    performance_result: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    analysis_config: Mapped[dict | None] = mapped_column(_JSON, nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User"] = relationship("User", back_populates="runs")  # type: ignore[name-defined]
