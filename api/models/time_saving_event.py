"""TimeSavingEvent ORM model — tracks individual time-saving events per user."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base

try:
    from sqlalchemy import JSON
    _JSON = JSON
except ImportError:
    from sqlalchemy import Text as _JSON  # type: ignore[assignment]


class TimeSavingEvent(Base):
    """One row per recorded automated operation that saved manual analyst work.

    Each event stores the *manual* time the operation would have taken if performed
    by hand (Excel/SQL/pivot tables) — that is the saving we credit to the user.
    """

    __tablename__ = "time_saving_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manual_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    scale_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    context: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("ix_time_saving_user_created", "user_id", "created_at"),
    )
