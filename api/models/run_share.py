"""RunShare ORM model — per-user access control for analysis runs."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class RunShare(Base):
    __tablename__ = "run_shares"
    __table_args__ = (UniqueConstraint("run_id", "shared_with_user_id"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shared_with_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="shares")  # type: ignore[name-defined]
    shared_with: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
