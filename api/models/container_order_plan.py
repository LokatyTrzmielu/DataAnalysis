"""ContainerOrderPlan ORM model — saved snapshots of Container Order calculations.

Each row is an explicit "Save plan" action from the user. Holds full snapshots
of the params and computed plan, plus a soft FK to the source AnalysisRun
(nullable so deleting the analysis doesn't cascade-kill saved plans).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

try:
    from sqlalchemy import JSON
    _JSON = JSON
except ImportError:
    from sqlalchemy import Text as _JSON  # type: ignore[assignment]


class ContainerOrderPlan(Base):
    __tablename__ = "container_order_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable: deleting the source AnalysisRun must NOT remove saved plans —
    # the user explicitly saved a snapshot and should still be able to view /
    # export it even after the source disappears.
    source_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # Full snapshots — JSON of PlanParamsRequest and ContainerPlanResponse.
    params: Mapped[dict] = mapped_column(_JSON, nullable=False)
    plan: Mapped[dict] = mapped_column(_JSON, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
