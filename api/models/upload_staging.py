"""UploadStaging ORM model (TTL 2h for uploaded files)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String

try:
    from sqlalchemy import JSON
    _JSON = JSON
except ImportError:
    from sqlalchemy import Text as _JSON  # type: ignore[assignment]

from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class UploadStaging(Base):
    __tablename__ = "upload_staging"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "masterdata" | "orders"
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    detected_columns: Mapped[list | None] = mapped_column(_JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
