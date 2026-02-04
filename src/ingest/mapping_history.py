"""Mapping History Service - learns from user corrections."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_HISTORY_PATH = Path(__file__).parent.parent / "core" / "mapping_history.yml"


@dataclass
class MappingHistoryEntry:
    """Single mapping history entry."""

    source_column: str  # Normalized column name
    target_field: str  # Target schema field (e.g., "sku")
    schema_type: str  # "masterdata" or "orders"
    client_pattern: str = ""  # Client name (optional)
    use_count: int = 1  # How many times used
    last_used: str = ""  # ISO timestamp
    is_user_correction: bool = False  # True if user manually corrected

    def __post_init__(self) -> None:
        if not self.last_used:
            self.last_used = datetime.now().isoformat()


class MappingHistoryService:
    """Service for managing mapping history."""

    def __init__(self, history_path: Optional[Path] = None) -> None:
        """Initialize service.

        Args:
            history_path: Path to history YAML file. Defaults to core/mapping_history.yml
        """
        self.history_path = history_path or DEFAULT_HISTORY_PATH
        self._cache: Optional[dict] = None

    def load_history(self) -> dict:
        """Load mapping history from YAML file.

        Returns:
            Dict with history data
        """
        if self._cache is not None:
            return self._cache

        if not self.history_path.exists():
            self._cache = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "masterdata_mappings": [],
                "orders_mappings": [],
                "blacklist": [],
            }
            return self._cache

        with open(self.history_path, "r", encoding="utf-8") as f:
            self._cache = yaml.safe_load(f) or {}

        # Ensure required keys exist
        if self._cache is not None:
            for key in ["masterdata_mappings", "orders_mappings", "blacklist"]:
                if key not in self._cache:
                    self._cache[key] = []

        return self._cache or {}

    def save_history(self) -> None:
        """Save mapping history to YAML file."""
        if self._cache is None:
            return

        self._cache["last_updated"] = datetime.now().isoformat()

        # Ensure parent directory exists
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.history_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self._cache,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def get_history_mappings(
        self, schema_type: str, client_pattern: str = ""
    ) -> list[MappingHistoryEntry]:
        """Get history mappings for schema type, sorted by priority.

        Args:
            schema_type: "masterdata" or "orders"
            client_pattern: Optional client name filter

        Returns:
            List of MappingHistoryEntry sorted by use_count descending
        """
        data = self.load_history()
        key = f"{schema_type}_mappings"
        entries = data.get(key, [])

        result = []
        for entry in entries:
            # Filter by client pattern if provided
            if client_pattern and entry.get("client_pattern"):
                if entry["client_pattern"] != client_pattern:
                    continue

            result.append(
                MappingHistoryEntry(
                    source_column=entry.get("source_column", ""),
                    target_field=entry.get("target_field", ""),
                    schema_type=schema_type,
                    client_pattern=entry.get("client_pattern", ""),
                    use_count=entry.get("use_count", 1),
                    last_used=entry.get("last_used", ""),
                    is_user_correction=entry.get("is_user_correction", False),
                )
            )

        # Sort by priority: use_count descending
        result.sort(key=lambda x: x.use_count, reverse=True)
        return result

    def record_mapping(
        self,
        source_column: str,
        target_field: str,
        schema_type: str,
        client_pattern: str = "",
        is_user_correction: bool = False,
    ) -> None:
        """Record a mapping (update if exists, create if new).

        Args:
            source_column: Source column name from file
            target_field: Target schema field (e.g., "sku")
            schema_type: "masterdata" or "orders"
            client_pattern: Optional client name
            is_user_correction: True if user manually corrected
        """
        data = self.load_history()
        key = f"{schema_type}_mappings"

        if key not in data:
            data[key] = []

        # Normalize source column
        normalized = self._normalize(source_column)

        # Check if entry exists
        for entry in data[key]:
            if (
                entry["source_column"] == normalized
                and entry["target_field"] == target_field
            ):
                # Update existing
                entry["use_count"] = entry.get("use_count", 0) + 1
                entry["last_used"] = datetime.now().isoformat()
                if is_user_correction:
                    entry["is_user_correction"] = True
                if client_pattern and not entry.get("client_pattern"):
                    entry["client_pattern"] = client_pattern
                self._cache = data
                return

        # Create new entry
        new_entry = {
            "source_column": normalized,
            "target_field": target_field,
            "client_pattern": client_pattern,
            "use_count": 1,
            "last_used": datetime.now().isoformat(),
            "is_user_correction": is_user_correction,
        }
        data[key].append(new_entry)
        self._cache = data

    def is_blacklisted(
        self, source_column: str, target_field: str, schema_type: str
    ) -> bool:
        """Check if mapping is blacklisted.

        Args:
            source_column: Source column name
            target_field: Target field
            schema_type: "masterdata" or "orders"

        Returns:
            True if blacklisted
        """
        data = self.load_history()
        normalized = self._normalize(source_column)

        for entry in data.get("blacklist", []):
            if (
                entry.get("source_column") == normalized
                and entry.get("target_field") == target_field
                and entry.get("schema_type") == schema_type
            ):
                return True
        return False

    def add_to_blacklist(
        self, source_column: str, target_field: str, schema_type: str
    ) -> None:
        """Add mapping to blacklist (user explicitly rejected).

        Args:
            source_column: Source column name
            target_field: Target field
            schema_type: "masterdata" or "orders"
        """
        data = self.load_history()
        normalized = self._normalize(source_column)

        # Check if already blacklisted
        for entry in data.get("blacklist", []):
            if (
                entry.get("source_column") == normalized
                and entry.get("target_field") == target_field
                and entry.get("schema_type") == schema_type
            ):
                return

        if "blacklist" not in data:
            data["blacklist"] = []

        data["blacklist"].append(
            {
                "source_column": normalized,
                "target_field": target_field,
                "schema_type": schema_type,
            }
        )
        self._cache = data

    def clear_cache(self) -> None:
        """Clear internal cache to force reload from file."""
        self._cache = None

    def _normalize(self, column_name: str) -> str:
        """Normalize column name for storage.

        Args:
            column_name: Original column name

        Returns:
            Normalized lowercase name with underscores
        """
        return column_name.lower().strip().replace(" ", "_").replace("-", "_")
