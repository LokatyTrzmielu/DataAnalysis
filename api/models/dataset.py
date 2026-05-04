"""Dataset ORM model — tracks imported datasets persisted as DuckDB files."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

try:
    from sqlalchemy import JSON
    _JSON = JSON
except ImportError:
    from sqlalchemy import Text as _JSON  # type: ignore[assignment]

from api.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # masterdata | orders
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duckdb_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    column_names: Mapped[list | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
