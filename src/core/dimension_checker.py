"""Dimension checking utility with rotation-aware fit validation."""

from itertools import permutations

from src.core.types import CarrierConfig


class DimensionChecker:
    """Check if item dimensions can fit in carriers with rotation.

    Uses the same 6-rotation logic as capacity analysis to ensure consistency
    between outlier detection and container fitting.
    """

    # 6 possible orientations (permutations of L, W, H)
    ORIENTATIONS = list(permutations(["L", "W", "H"]))

    @staticmethod
    def can_fit_any_carrier(
        length_mm: float,
        width_mm: float,
        height_mm: float,
        carriers: list[CarrierConfig],
    ) -> bool:
        """Check if item can fit in ANY carrier with ANY rotation.

        Args:
            length_mm: Item length in mm
            width_mm: Item width in mm
            height_mm: Item height in mm
            carriers: List of carrier configurations

        Returns:
            True if item fits in at least one active carrier with some orientation
        """
        if not carriers:
            return True  # No carriers = no dimensional constraints

        dims = {"L": length_mm, "W": width_mm, "H": height_mm}

        for carrier in carriers:
            if not carrier.is_active:
                continue

            for orientation in DimensionChecker.ORIENTATIONS:
                sku_x = dims[orientation[0]]
                sku_y = dims[orientation[1]]
                sku_z = dims[orientation[2]]

                if (
                    sku_x <= carrier.inner_length_mm
                    and sku_y <= carrier.inner_width_mm
                    and sku_z <= carrier.inner_height_mm
                ):
                    return True

        return False

    @staticmethod
    def get_max_allowed_dimension(carriers: list[CarrierConfig]) -> float:
        """Get maximum dimension that could fit in any active carrier.

        Args:
            carriers: List of carrier configurations

        Returns:
            Maximum inner dimension across all active carriers
        """
        max_dim = 0.0
        for carrier in carriers:
            if carrier.is_active:
                max_dim = max(
                    max_dim,
                    carrier.inner_length_mm,
                    carrier.inner_width_mm,
                    carrier.inner_height_mm,
                )
        return max_dim
