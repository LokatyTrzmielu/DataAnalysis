"""Modele danych Pydantic dla aplikacji DataAnalysis."""

from datetime import datetime, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enumy
# ============================================================================


class DataQualityFlag(str, Enum):
    """Flaga jakosci danych - czy wartosc jest oryginalna czy oszacowana."""

    RAW = "RAW"  # Oryginalna wartosc z danych
    ESTIMATED = "ESTIMATED"  # Wartosc uzupelniona przez imputacje


class FitResult(str, Enum):
    """Wynik dopasowania SKU do nosnika."""

    FIT = "FIT"  # Miesci sie
    BORDERLINE = "BORDERLINE"  # Miesci sie, ale blisko granicy (< threshold)
    NOT_FIT = "NOT_FIT"  # Nie miesci sie


class OrientationConstraint(str, Enum):
    """Ograniczenie orientacji SKU na nosniku."""

    ANY = "ANY"  # Dowolna orientacja (6 mozliwosci)
    UPRIGHT_ONLY = "UPRIGHT_ONLY"  # Tylko pionowo (wysokosc jako Z)
    FLAT_ONLY = "FLAT_ONLY"  # Tylko plasko (wysokosc jako najmniejszy wymiar)


class ShiftType(str, Enum):
    """Typ zmiany roboczej."""

    BASE = "base"  # Normalna zmiana
    OVERLAY = "overlay"  # Dodatkowa zmiana (nadgodziny, peak season)


class LimitingFactor(str, Enum):
    """Czynnik limitujacy pojemnosc."""

    DIMENSION = "DIMENSION"  # Ograniczenie gabarytowe
    WEIGHT = "WEIGHT"  # Ograniczenie wagowe
    NONE = "NONE"  # Brak ograniczenia


# ============================================================================
# Masterdata
# ============================================================================


class MasterdataRow(BaseModel):
    """Wiersz danych Masterdata (SKU)."""

    sku: str = Field(..., description="Unikalny identyfikator SKU")

    # Wymiary w mm
    length_mm: float = Field(..., ge=0, description="Dlugosc w mm")
    width_mm: float = Field(..., ge=0, description="Szerokosc w mm")
    height_mm: float = Field(..., ge=0, description="Wysokosc w mm")

    # Waga w kg
    weight_kg: float = Field(..., ge=0, description="Waga w kg")

    # Zapas
    stock_qty: int = Field(default=0, ge=0, description="Ilosc na stanie (EA)")

    # Flagi jakosci danych
    length_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    width_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    height_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    weight_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)
    stock_flag: DataQualityFlag = Field(default=DataQualityFlag.RAW)

    # Ograniczenie orientacji
    orientation_constraint: OrientationConstraint = Field(
        default=OrientationConstraint.ANY
    )

    @property
    def volume_m3(self) -> float:
        """Oblicz kubature w m3."""
        return (self.length_mm * self.width_mm * self.height_mm) / 1_000_000_000

    @property
    def has_estimated_dimensions(self) -> bool:
        """Czy ktorys z wymiarow zostal oszacowany."""
        return any(
            flag == DataQualityFlag.ESTIMATED
            for flag in [self.length_flag, self.width_flag, self.height_flag]
        )

    @property
    def has_estimated_weight(self) -> bool:
        """Czy waga zostala oszacowana."""
        return self.weight_flag == DataQualityFlag.ESTIMATED


class MasterdataStats(BaseModel):
    """Statystyki zbiorowe dla Masterdata."""

    total_sku_count: int = Field(..., ge=0)
    sku_with_dimensions: int = Field(..., ge=0)
    sku_with_weight: int = Field(..., ge=0)
    sku_with_stock: int = Field(..., ge=0)

    # Pokrycie danych (%)
    dimensions_coverage_pct: float = Field(..., ge=0, le=100)
    weight_coverage_pct: float = Field(..., ge=0, le=100)
    stock_coverage_pct: float = Field(..., ge=0, le=100)

    # Imputacja
    sku_with_estimated_dimensions: int = Field(default=0, ge=0)
    sku_with_estimated_weight: int = Field(default=0, ge=0)


# ============================================================================
# Orders
# ============================================================================


class OrderRow(BaseModel):
    """Wiersz danych zamowienia."""

    order_id: str = Field(..., description="Identyfikator zamowienia")
    line_id: Optional[str] = Field(default=None, description="Identyfikator linii")
    sku: str = Field(..., description="SKU produktu")
    quantity: int = Field(..., ge=1, description="Ilosc w linii (EA)")
    timestamp: datetime = Field(..., description="Timestamp realizacji/wysylki")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: str | datetime) -> datetime:
        """Parsuj timestamp z roznych formatow."""
        if isinstance(v, datetime):
            return v
        # Probuj rozne formaty
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
        raise ValueError(f"Nie mozna sparsowac daty: {v}")


class OrderStats(BaseModel):
    """Statystyki zbiorowe dla Orders."""

    total_orders: int = Field(..., ge=0)
    total_lines: int = Field(..., ge=0)
    total_units: int = Field(..., ge=0)
    unique_sku: int = Field(..., ge=0)

    # Przedzialy czasowe
    date_from: datetime
    date_to: datetime

    # Srednie
    avg_lines_per_order: float = Field(..., ge=0)
    avg_units_per_line: float = Field(..., ge=0)
    avg_units_per_order: float = Field(..., ge=0)


# ============================================================================
# Carriers (Nosniki Kardex)
# ============================================================================


class CarrierConfig(BaseModel):
    """Konfiguracja nosnika Kardex."""

    carrier_id: str = Field(..., description="Identyfikator nosnika")
    name: str = Field(..., description="Nazwa nosnika")

    # Wymiary wewnetrzne w mm
    inner_length_mm: float = Field(..., gt=0)
    inner_width_mm: float = Field(..., gt=0)
    inner_height_mm: float = Field(..., gt=0)

    # Limit wagowy
    max_weight_kg: float = Field(..., gt=0)

    # Czy aktywny
    is_active: bool = Field(default=True)

    @property
    def inner_volume_m3(self) -> float:
        """Objetosc wewnetrzna w m3."""
        return (
            self.inner_length_mm * self.inner_width_mm * self.inner_height_mm
        ) / 1_000_000_000


class CarrierFitResult(BaseModel):
    """Wynik dopasowania SKU do nosnika."""

    sku: str
    carrier_id: str
    fit_status: FitResult
    best_orientation: Optional[tuple[str, str, str]] = Field(
        default=None, description="Najlepsza orientacja (L, W, H) -> (X, Y, Z)"
    )
    units_per_carrier: int = Field(default=0, ge=0)
    limiting_factor: LimitingFactor = Field(default=LimitingFactor.NONE)
    margin_mm: Optional[float] = Field(
        default=None, description="Margines do granicy w mm (dla BORDERLINE)"
    )


# ============================================================================
# Shifts (Zmiany robocze)
# ============================================================================


class ShiftConfig(BaseModel):
    """Konfiguracja pojedynczej zmiany."""

    name: str = Field(..., description="Nazwa zmiany (np. S1, S2, OT_N)")
    start: time = Field(..., description="Godzina rozpoczecia")
    end: time = Field(..., description="Godzina zakonczenia")
    shift_type: ShiftType = Field(default=ShiftType.BASE)

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_time(cls, v: str | time) -> time:
        """Parsuj czas z stringa."""
        if isinstance(v, time):
            return v
        try:
            return datetime.strptime(v, "%H:%M").time()
        except ValueError:
            return datetime.strptime(v, "%H:%M:%S").time()

    @property
    def duration_hours(self) -> float:
        """Czas trwania zmiany w godzinach."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute

        # Obsluga zmiany nocnej (przechodzi przez polnoc)
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60

        return (end_minutes - start_minutes) / 60


class WeeklySchedule(BaseModel):
    """Harmonogram tygodniowy."""

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
        """Pobierz zmiany dla dnia tygodnia (0=pon, 6=niedz)."""
        days = [self.mon, self.tue, self.wed, self.thu, self.fri, self.sat, self.sun]
        return days[weekday]

    @property
    def total_base_hours_per_week(self) -> float:
        """Suma godzin base shifts w tygodniu."""
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
    """Problem jakosci danych."""

    sku: str
    issue_type: str = Field(..., description="Typ problemu: missing, outlier, duplicate, etc.")
    field: str = Field(..., description="Pole z problemem")
    original_value: Optional[str] = Field(default=None)
    imputed_value: Optional[str] = Field(default=None)
    severity: str = Field(default="warning", description="critical, warning, info")


class DQScorecard(BaseModel):
    """Data Quality Scorecard."""

    total_records: int = Field(..., ge=0)

    # Pokrycie danych
    dimensions_coverage_pct: float = Field(..., ge=0, le=100)
    weight_coverage_pct: float = Field(..., ge=0, le=100)
    stock_coverage_pct: float = Field(..., ge=0, le=100)

    # Liczby problemow
    missing_critical_count: int = Field(default=0, ge=0)
    suspect_outliers_count: int = Field(default=0, ge=0)
    high_risk_borderline_count: int = Field(default=0, ge=0)
    duplicates_count: int = Field(default=0, ge=0)
    conflicts_count: int = Field(default=0, ge=0)
    collisions_count: int = Field(default=0, ge=0)

    # Imputacja
    imputed_dimensions_count: int = Field(default=0, ge=0)
    imputed_weight_count: int = Field(default=0, ge=0)

    @property
    def overall_score(self) -> float:
        """Oblicz ogolny wynik jakosci (0-100)."""
        # Srednia wazona pokrycia
        coverage = (
            self.dimensions_coverage_pct * 0.4
            + self.weight_coverage_pct * 0.3
            + self.stock_coverage_pct * 0.3
        )
        # Kara za problemy
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
