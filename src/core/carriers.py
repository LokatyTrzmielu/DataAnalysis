"""Carrier configuration loading and persistence."""

from pathlib import Path
from typing import Optional

import yaml

from src.core.types import CarrierConfig


# Default path for carriers configuration
DEFAULT_CARRIERS_PATH = Path(__file__).parent / "carriers.yml"


class CarrierService:
    """Service for managing carrier configurations."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize service.

        Args:
            config_path: Path to carriers.yml. Uses default if None.
        """
        self.config_path = config_path or DEFAULT_CARRIERS_PATH

    def load_all_carriers(self) -> list[CarrierConfig]:
        """Load all carriers (predefined + custom saved).

        Returns:
            List of CarrierConfig objects
        """
        if not self.config_path.exists():
            return self._get_default_carriers()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            return self._get_default_carriers()

        carriers = []

        # Load predefined carriers
        for c in data.get("carriers", []):
            c["is_predefined"] = True
            carriers.append(CarrierConfig(**c))

        # Load saved custom carriers
        for c in data.get("custom_carriers", []):
            c["is_predefined"] = False
            carriers.append(CarrierConfig(**c))

        return carriers

    def save_custom_carriers(self, carriers: list[CarrierConfig]) -> None:
        """Save custom carriers to the config file.

        Args:
            carriers: List of custom carriers to save (is_predefined=False)
        """
        # Load existing data
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {"carriers": [], "custom_carriers": []}

        # Filter only non-predefined carriers
        custom_to_save = [c for c in carriers if not c.is_predefined]

        # Convert to dict format
        data["custom_carriers"] = [
            {
                "carrier_id": c.carrier_id,
                "name": c.name,
                "inner_length_mm": c.inner_length_mm,
                "inner_width_mm": c.inner_width_mm,
                "inner_height_mm": c.inner_height_mm,
                "max_weight_kg": c.max_weight_kg,
                "is_active": c.is_active,
            }
            for c in custom_to_save
        ]

        # Write back
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

    def _get_default_carriers(self) -> list[CarrierConfig]:
        """Return hardcoded default carriers if file doesn't exist."""
        return [
            CarrierConfig(
                carrier_id="NOSNIK_1",
                name="Nosnik 1 - 600x400x220",
                inner_length_mm=570,
                inner_width_mm=370,
                inner_height_mm=200,
                max_weight_kg=35,
                is_active=True,
                is_predefined=True,
            ),
            CarrierConfig(
                carrier_id="NOSNIK_2",
                name="Nosnik 2 - 640x440x238",
                inner_length_mm=610,
                inner_width_mm=410,
                inner_height_mm=210,
                max_weight_kg=35,
                is_active=True,
                is_predefined=True,
            ),
            CarrierConfig(
                carrier_id="NOSNIK_3",
                name="Nosnik 3 - 3650x864x200",
                inner_length_mm=3650,
                inner_width_mm=864,
                inner_height_mm=200,
                max_weight_kg=440,
                is_active=True,
                is_predefined=True,
            ),
        ]


def load_carriers(config_path: Optional[Path] = None) -> list[CarrierConfig]:
    """Helper function to load all carriers.

    Args:
        config_path: Optional path to carriers.yml

    Returns:
        List of CarrierConfig objects
    """
    service = CarrierService(config_path)
    return service.load_all_carriers()
