"""Pydantic data models for DataAnalysis application."""

from datetime import datetime, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class DataQualityFlag(str, Enum):
    """Data quality flag - whether value is original or estimated."""

    RAW = "RAW"  # Original value from data
    ESTIMATED = "ESTIMATED"  # Value filled by imputation


class FitResult(str, Enum):
    """SKU fit result for carrier."""

    FIT = "FIT"  # Fits
    BORDERLINE = "BORDERLINE"  # Fits, but close to limit (< threshold)
    NOT_FIT = "NOT_FIT"  # Does not fit


class OrientationConstraint(str, Enum):
    """SKU orientation constraint on carrier."""

    ANY = "ANY"  # Any orientation (6 possibilities)
    UPRIGHT_ONLY = "UPRIGHT_ONLY"  # Only upright (height as Z)
    FLAT_ONLY = "FLAT_ONLY"  # Only flat (height as smallest dimension)


class ShiftType(str, Enum):
    """Work shift type."""

    BASE = "base"  # Normal shift
    OVERLAY = "overlay"  # Additional shift (overtime, peak season)


class LimitingFactor(str, Enum):
    """Capacity limiting factor."""

    DIMENSION = "DIMENSION"  # Dimensional constraint
    WEIGHT = "WEIGHT"  # Weight constraint
    NONE = "NONE"  # No constraint


# ============================================================================
# Masterdata
# ============================================================================


class MasterdataRow(BaseModel):
    """Masterdata row (SKU)."""

    sku: str = Field(..., description="Unique SKU identifier")

    # Dimensions in mm
    length_mm: float = Field(..., ge=0, description="Length in mm")
    width_mm: float = Field(..., ge=0, description="Width in mm")
    height_mm: float = Field(..., ge=0, description="Height in mm")

    # Weight in kg
    weight_kg: float = Field(..., ge=0, description="Weight in kg")

    # Stock
    stock_qty: int = Field(default=0, ge=0, description="Stock quantity (EA)")

    # Data quality flags
    length_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    width_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    height_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    weight_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    stock_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)

    # Orientation constraint
    orientation_constraint: OrientationConstraint = Field(
        default=OrientationConstraint.ANY
    )

    @property
    def volume_m3(self) -> float:
        """Calculate volume in m3."""
        return (self.length_mm * self.width_mm * self.height_mm) / 1_000_000_000

    @property
    def has_estimated_dimensions(self) -> bool:
        """Whether any dimension was estimated."""
        return any(
            flag == DataQualityFlag.ESTIMATED
            for flag in [self.length_flag, self.width_flag, self.height_flag]
        )

    @property
    def has_estimated_weight(self) -> bool:
        """Whether weight was estimated."""
        return self.weight_flag == DataQualityFlag.ESTIMATED


class MasterdataStats(BaseModel):
    """Aggregate statistics for Masterdata."""

    total_sku_count: int = Field(..., ge=0)
    sku_with_dimensions: int = Field(..., ge=0)
    sku_with_weight: int = Field(..., ge=0)
    sku_with_stock: int = Field(..., ge=0)

    # Data coverage (%)
    dimensions_coverage_pct: float = Field(..., ge=0, le=100)
    weight_coverage_pct: float = Field(..., ge=0, le=100)
    stock_coverage_pct: float = Field(..., ge=0, le=100)

    # Imputation
    sku_with_estimated_dimensions: int = Field(default=0, ge=0)
    sku_with_estimated_weight: int = Field(default=0, ge=0)


# ============================================================================
# Orders
# ============================================================================


class OrderRow(BaseModel):
    """Order data row."""

    order_id: str = Field(..., description="Order identifier")
    line_id: Optional[str] = Field(default=None, description="Line identifier")
    sku: str = Field(..., description="Product SKU")
    quantity: int = Field(..., ge=1, description="Line quantity (EA)")
    timestamp: datetime = Field(..., description="Fulfillment/shipping timestamp")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: str | datetime) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        # Try various formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {v}")


class OrderStats(BaseModel):
    """Aggregate statistics for Orders."""

    total_orders: int = Field(..., ge=0)
    total_lines: int = Field(..., ge=0)
    total_units: int = Field(..., ge=0)
    unique_sku: int = Field(..., ge=0)

    # Time ranges
    date_from: datetime
    date_to: datetime

    # Averages
    avg_lines_per_order: float = Field(..., ge=0)
    avg_units_per_line: float = Field(..., ge=0)
    avg_units_per_order: float = Field(..., ge=0)


# ============================================================================
# Carriers (Kardex Carriers)
# ============================================================================


class CarrierConfig(BaseModel):
    """Kardex carrier configuration."""

    carrier_id: str = Field(..., description="Carrier identifier")
    name: str = Field(..., description="Carrier name")

    # Internal dimensions in mm
    inner_length_mm: float = Field(..., gt=0)
    inner_width_mm: float = Field(..., gt=0)
    inner_height_mm: float = Field(..., gt=0)

    # Weight limit
    max_weight_kg: float = Field(..., gt=0)

    # Whether active
    is_active: bool = Field(default=True)

    # Whether this is a predefined carrier (cannot be deleted)
    is_predefined: bool = Field(default=False)

    @property
    def inner_volume_m3(self) -> float:
        """Internal volume in m3."""
        return (
            self.inner_length_mm * self.inner_width_mm * self.inner_height_mm
        ) / 1_000_000_000


class CarrierFitResult(BaseModel):
    """SKU fit result for carrier."""

    sku: str
    carrier_id: str
    fit_status: FitResult
    best_orientation: Optional[tuple[str, str, str]] = Field(
        default=None, description="Best orientation (L, W, H) -> (X, Y, Z)"
    )
    units_per_carrier: int = Field(default=0, ge=0)
    limiting_factor: LimitingFactor = Field(default=LimitingFactor.NONE)
    margin_mm: Optional[float] = Field(
        default=None, description="Margin to limit in mm (for BORDERLINE)"
    )


# ============================================================================
# Shifts (Work shifts)
# ============================================================================


class ShiftConfig(BaseModel):
    """Single shift configuration."""

    name: str = Field(..., description="Shift name (e.g., S1, S2, OT_N)")
    start: time = Field(..., description="Start time")
    end: time = Field(..., description="End time")
    shift_type: ShiftType = Field(default=ShiftType.BASE)

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_time(cls, v: str | time) -> time:
        """Parse time from string."""
        if isinstance(v, time):
            return v
        try:
            return datetime.strptime(v, "%H:%M").time()
        except ValueError:
            return datetime.strptime(v, "%H:%M:%S").time()

    @property
    def duration_hours(self) -> float:
        """Shift duration in hours."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute

        # Handle night shift (crosses midnight)
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60

        return (end_minutes - start_minutes) / 60


class WeeklySchedule(BaseModel):
    """Weekly schedule."""

    timezone: str = Field(default="Europe/Warsaw")
    productive_hours_per_shift: float = Field(default=7.0, gt=0, le=24)

    mon: list[ShiftConfig] = Field(default_factory=list)
    tue: list[ShiftConfig] = Field(default_factory=list)
    wed: list[ShiftConfig] = Field(default_factory=list)
    thu: list[ShiftConfig] = Field(default_factory=list)
    fri: list[ShiftConfig] = Field(default_factory=list)
    sat: list[ShiftConfig] = Field(default_factory=list)
    sun: list[ShiftConfig] = Field(default_factory=list)

    def get_shifts_for_day(self, weekday: int) -> list[ShiftConfig]:
        """Get shifts for day of week (0=Mon, 6=Sun)."""
        days = [self.mon, self.tue, self.wed, self.thu, self.fri, self.sat, self.sun]
        return days[weekday]

    @property
    def total_base_hours_per_week(self) -> float:
        """Sum of base shift hours per week."""
        total = 0.0
        for shifts in [self.mon, self.tue, self.wed, self.thu, self.fri, self.sat, self.sun]:
            for shift in shifts:
                if shift.shift_type == ShiftType.BASE:
                    total += shift.duration_hours
        return total


# ============================================================================
# Data Quality
# ============================================================================


class DQIssue(BaseModel):
    """Data quality issue."""

    sku: str
    issue_type: str = Field(..., description="Issue type: missing, outlier, duplicate, etc.")
    field: str = Field(..., description="Field with issue")
    original_value: Optional[str] = Field(default=None)
    imputed_value: Optional[str] = Field(default=None)
    severity: str = Field(default="warning", description="critical, warning, info")


class DQScorecard(BaseModel):
    """Data Quality Scorecard."""

    total_records: int = Field(..., ge=0)

    # Data coverage
    dimensions_coverage_pct: float = Field(..., ge=0, le=100)
    weight_coverage_pct: float = Field(..., ge=0, le=100)
    stock_coverage_pct: float = Field(..., ge=0, le=100)

    # Issue counts
    missing_critical_count: int = Field(default=0, ge=0)
    suspect_outliers_count: int = Field(default=0, ge=0)
    high_risk_borderline_count: int = Field(default=0, ge=0)
    duplicates_count: int = Field(default=0, ge=0)
    conflicts_count: int = Field(default=0, ge=0)
    collisions_count: int = Field(default=0, ge=0)

    # Imputation
    imputed_dimensions_count: int = Field(default=0, ge=0)
    imputed_weight_count: int = Field(default=0, ge=0)

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        # Weighted average of coverage
        coverage = (
            self.dimensions_coverage_pct * 0.4
            + self.weight_coverage_pct * 0.3
            + self.stock_coverage_pct * 0.3
        )
        # Penalty for issues
        problem_penalty = min(
            50,
            (self.missing_critical_count * 2)
            + (self.suspect_outliers_count * 1)
            + (self.high_risk_borderline_count * 0.5)
            + (self.duplicates_count * 1)
            + (self.conflicts_count * 2)
            + (self.collisions_count * 3),
        )
        return max(0, coverage - problem_penalty)
