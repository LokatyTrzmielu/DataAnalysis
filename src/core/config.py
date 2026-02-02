"""DataAnalysis application configuration constants."""

from dataclasses import dataclass, field
from typing import Final


# ============================================================================
# Data Quality - Value treatment
# ============================================================================

TREAT_ZERO_AS_MISSING_DIMENSIONS: Final[bool] = True
TREAT_ZERO_AS_MISSING_WEIGHT: Final[bool] = True
TREAT_ZERO_AS_MISSING_QUANTITIES: Final[bool] = True
TREAT_NEGATIVE_AS_MISSING: Final[bool] = True
TREAT_INVALID_PARSING_AS_MISSING: Final[bool] = True

# ============================================================================
# Imputation
# ============================================================================

IMPUTATION_ENABLED: Final[bool] = True
IMPUTATION_METHOD: Final[str] = "median"  # median, mean, mode
IMPUTATION_SCOPE: Final[str] = "global"   # global, per_category

# ============================================================================
# Capacity Analysis - Thresholds
# ============================================================================

BORDERLINE_THRESHOLD_MM: Final[float] = 2.0  # mm - threshold for BORDERLINE fit

# ============================================================================
# Outlier Detection - Unified thresholds
# ============================================================================

# Fallback thresholds used when no carriers are configured.
# When carriers are configured, dimensional outliers (length, width, height)
# are detected using rotation-aware checking - an item is only an outlier
# if it cannot fit in ANY active carrier with ANY of 6 possible rotations.
#
# Note: Width and height max values are set to typical carrier constraints,
# while length max remains at largest carrier dimension (3650mm).
OUTLIER_THRESHOLDS: Final[dict[str, dict[str, float]]] = {
    "length_mm": {"min": 0.001, "max": 3650.0},
    "width_mm": {"min": 0.001, "max": 864.0},
    "height_mm": {"min": 0.001, "max": 500.0},
    "weight_kg": {"min": 0.001, "max": 500.0},
    "stock_qty": {"min": 0.0, "max": 1_000_000.0},
}

# ============================================================================
# Machine Utilization - Default values
# ============================================================================

DEFAULT_UTILIZATION_VLM: Final[float] = 0.75  # Vertical Lift Module
DEFAULT_UTILIZATION_MIB: Final[float] = 0.68  # Mini-load in Box

# ============================================================================
# Performance Analysis - Default values
# ============================================================================

DEFAULT_PRODUCTIVE_HOURS_PER_SHIFT: Final[float] = 7.0  # from 8h shift
DEFAULT_SHIFT_DURATION_HOURS: Final[float] = 8.0

# ============================================================================
# Percentiles for Peak Analysis
# ============================================================================

PEAK_PERCENTILES: Final[tuple[int, ...]] = (90, 95, 99)

# ============================================================================
# CSV Export
# ============================================================================

CSV_SEPARATOR: Final[str] = ";"
CSV_ENCODING: Final[str] = "utf-8-sig"  # UTF-8 with BOM
CSV_NEWLINE: Final[str] = "\r\n"  # CRLF (Windows)

# ============================================================================
# Number formatting - decimal places
# ============================================================================

DECIMAL_PLACES_VOLUME_M3: Final[int] = 6
DECIMAL_PLACES_WEIGHT_KG: Final[int] = 3
DECIMAL_PLACES_PERCENT: Final[int] = 2
DECIMAL_PLACES_RATE: Final[int] = 3  # for /hour, /day, /shift
DECIMAL_PLACES_AVERAGE: Final[int] = 3
DECIMAL_PLACES_RATIO: Final[int] = 3

# ============================================================================
# Dates
# ============================================================================

DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DEFAULT_TIMEZONE: Final[str] = "Europe/Warsaw"

# ============================================================================
# Performance limits
# ============================================================================

MAX_SKU_COUNT: Final[int] = 200_000
MAX_ORDER_LINES: Final[int] = 2_000_000


@dataclass
class Config:
    """Configurable analysis parameters."""

    # Data Quality
    treat_zero_as_missing_dimensions: bool = TREAT_ZERO_AS_MISSING_DIMENSIONS
    treat_zero_as_missing_weight: bool = TREAT_ZERO_AS_MISSING_WEIGHT
    treat_zero_as_missing_quantities: bool = TREAT_ZERO_AS_MISSING_QUANTITIES
    treat_negative_as_missing: bool = TREAT_NEGATIVE_AS_MISSING

    # Imputation
    imputation_enabled: bool = IMPUTATION_ENABLED
    imputation_method: str = IMPUTATION_METHOD

    # Capacity
    borderline_threshold_mm: float = BORDERLINE_THRESHOLD_MM
    utilization_vlm: float = DEFAULT_UTILIZATION_VLM
    utilization_mib: float = DEFAULT_UTILIZATION_MIB

    # Performance
    productive_hours_per_shift: float = DEFAULT_PRODUCTIVE_HOURS_PER_SHIFT

    # Percentiles
    peak_percentiles: tuple[int, ...] = field(default_factory=lambda: PEAK_PERCENTILES)

    def __post_init__(self) -> None:
        """Parameter validation."""
        if not 0 < self.utilization_vlm <= 1:
            raise ValueError(f"utilization_vlm must be in range (0, 1], got {self.utilization_vlm}")
        if not 0 < self.utilization_mib <= 1:
            raise ValueError(f"utilization_mib must be in range (0, 1], got {self.utilization_mib}")
        if not 0 < self.productive_hours_per_shift <= 24:
            raise ValueError(f"productive_hours_per_shift must be in range (0, 24], got {self.productive_hours_per_shift}")
        if self.borderline_threshold_mm < 0:
            raise ValueError(f"borderline_threshold_mm cannot be negative, got {self.borderline_threshold_mm}")
