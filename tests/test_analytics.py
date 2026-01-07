"""Testy jednostkowe dla modulu analytics."""

from datetime import datetime, date, time
from pathlib import Path

import polars as pl
import pytest

from src.analytics.capacity import (
    CapacityAnalyzer,
    analyze_capacity,
)
from src.analytics.shifts import (
    ShiftSchedule,
    ShiftScheduleLoader,
    ShiftInstance,
    load_shifts,
)
from src.analytics.performance import (
    PerformanceAnalyzer,
    analyze_performance,
    PerformanceKPI,
)
from src.core.types import (
    CarrierConfig,
    FitResult,
    OrientationConstraint,
    LimitingFactor,
    ShiftConfig,
    ShiftType,
    WeeklySchedule,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Testy CapacityAnalyzer
# ============================================================================


class TestCapacityAnalyzer:
    """Testy dla CapacityAnalyzer."""

    def get_test_carriers(self) -> list[CarrierConfig]:
        """Pobierz testowe nosniki."""
        return [
            CarrierConfig(
                carrier_id="TRAY_S",
                name="Tray Small",
                inner_length_mm=600,
                inner_width_mm=400,
                inner_height_mm=100,
                max_weight_kg=50,
            ),
            CarrierConfig(
                carrier_id="TRAY_M",
                name="Tray Medium",
                inner_length_mm=600,
                inner_width_mm=400,
                inner_height_mm=200,
                max_weight_kg=80,
            ),
        ]

    def test_analyze_sku_fit(self):
        """Test dopasowania SKU - miesci sie."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        results = analyzer.analyze_sku(
            sku="SKU1",
            length_mm=100,
            width_mm=80,
            height_mm=50,
            weight_kg=5,
        )

        assert len(results) == 2
        assert all(r.fit_status == FitResult.FIT for r in results)

    def test_analyze_sku_not_fit_dimension(self):
        """Test dopasowania SKU - nie miesci sie gabarytowo."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        results = analyzer.analyze_sku(
            sku="SKU2",
            length_mm=700,  # Za dlugi
            width_mm=80,
            height_mm=50,
            weight_kg=5,
        )

        assert all(r.fit_status == FitResult.NOT_FIT for r in results)
        assert all(r.limiting_factor == LimitingFactor.DIMENSION for r in results)

    def test_analyze_sku_not_fit_weight(self):
        """Test dopasowania SKU - nie miesci sie wagowo."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        results = analyzer.analyze_sku(
            sku="SKU3",
            length_mm=100,
            width_mm=80,
            height_mm=50,
            weight_kg=100,  # Za ciezki
        )

        # Oba nosniki maja limit < 100kg
        assert all(r.fit_status == FitResult.NOT_FIT for r in results)
        assert all(r.limiting_factor == LimitingFactor.WEIGHT for r in results)

    def test_analyze_sku_borderline(self):
        """Test dopasowania SKU - BORDERLINE."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers, borderline_threshold_mm=5)

        results = analyzer.analyze_sku(
            sku="SKU4",
            length_mm=598,  # Tylko 2mm marginesu
            width_mm=80,
            height_mm=50,
            weight_kg=5,
        )

        assert any(r.fit_status == FitResult.BORDERLINE for r in results)

    def test_analyze_sku_orientation_constraint_upright(self):
        """Test ograniczenia orientacji - UPRIGHT_ONLY."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        # SKU wyzszy niz TRAY_S (100mm) ale miesci sie do TRAY_M (200mm)
        results = analyzer.analyze_sku(
            sku="SKU5",
            length_mm=50,
            width_mm=50,
            height_mm=150,  # Wysokosc wieksza niz TRAY_S
            weight_kg=5,
            constraint=OrientationConstraint.UPRIGHT_ONLY,
        )

        # TRAY_S - nie miesci sie (height 150 > carrier height 100)
        # TRAY_M - miesci sie (height 150 < carrier height 200)
        tray_s_result = [r for r in results if r.carrier_id == "TRAY_S"][0]
        tray_m_result = [r for r in results if r.carrier_id == "TRAY_M"][0]

        assert tray_s_result.fit_status == FitResult.NOT_FIT
        assert tray_m_result.fit_status == FitResult.FIT

    def test_calculate_units_per_carrier(self):
        """Test obliczania liczby jednostek na nosniku."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        results = analyzer.analyze_sku(
            sku="SKU6",
            length_mm=100,  # 600/100 = 6 w dlugosci
            width_mm=100,   # 400/100 = 4 w szerokosci
            height_mm=50,   # 100/50 = 2 w wysokosci (TRAY_S)
            weight_kg=1,
        )

        tray_s_result = [r for r in results if r.carrier_id == "TRAY_S"][0]
        # 6 * 4 * 2 = 48 sztuk (ograniczenie gabarytowe)
        # 50kg / 1kg = 50 sztuk (ograniczenie wagowe)
        # min(48, 50) = 48
        assert tray_s_result.units_per_carrier == 48

    def test_analyze_dataframe(self):
        """Test analizy calego DataFrame."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 700.0, 100.0],  # SKU2 za dlugi
            "width_mm": [80.0, 80.0, 80.0],
            "height_mm": [50.0, 50.0, 50.0],
            "weight_kg": [5.0, 5.0, 5.0],
        })

        result = analyzer.analyze_dataframe(df)

        assert result.total_sku == 3
        assert result.fit_count > 0
        assert result.not_fit_count > 0
        assert len(result.carriers_analyzed) == 2

    def test_analyze_dataframe_carrier_stats(self):
        """Test statystyk per nosnik w analizie DataFrame."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 700.0, 100.0],  # SKU2 za dlugi
            "width_mm": [80.0, 80.0, 80.0],
            "height_mm": [50.0, 50.0, 50.0],
            "weight_kg": [5.0, 5.0, 5.0],
        })

        result = analyzer.analyze_dataframe(df)

        # Sprawdz czy carrier_stats zawiera statystyki dla kazdego nosnika
        assert len(result.carrier_stats) == 2
        assert "TRAY_S" in result.carrier_stats
        assert "TRAY_M" in result.carrier_stats

        # Sprawdz struktury CarrierStats
        tray_s_stats = result.carrier_stats["TRAY_S"]
        assert tray_s_stats.carrier_id == "TRAY_S"
        assert tray_s_stats.carrier_name == "Tray Small"
        assert tray_s_stats.fit_count >= 0
        assert tray_s_stats.borderline_count >= 0
        assert tray_s_stats.not_fit_count >= 0
        assert 0 <= tray_s_stats.fit_percentage <= 100
        assert tray_s_stats.total_volume_m3 >= 0

    def test_analyze_dataframe_volume_m3(self):
        """Test obliczania volume_m3 w wynikach analizy."""
        carriers = self.get_test_carriers()
        analyzer = CapacityAnalyzer(carriers)

        df = pl.DataFrame({
            "sku": ["SKU1"],
            "length_mm": [100.0],
            "width_mm": [100.0],
            "height_mm": [50.0],  # 0.5 litra = 0.0005 m3 per jednostka
            "weight_kg": [1.0],
        })

        result = analyzer.analyze_dataframe(df)

        # Sprawdz czy kolumna volume_m3 istnieje w wynikowym DataFrame
        assert "volume_m3" in result.df.columns

        # Sprawdz czy wartosci sa poprawnie obliczone
        # SKU1: 100*100*50 mm3 = 0.0005 m3 per jednostka
        # volume_m3 przechowuje objetosc JEDNOSTKOWA, nie calkowita
        fitting_rows = result.df.filter(
            (pl.col("sku") == "SKU1") &
            (pl.col("carrier_id") == "TRAY_S") &
            (pl.col("fit_status").is_in(["FIT", "BORDERLINE"]))
        )
        assert fitting_rows.height > 0
        volume = fitting_rows["volume_m3"][0]
        assert volume == pytest.approx(0.0005, rel=0.01)  # Objetosc jednostkowa

    def test_analyze_capacity_helper(self):
        """Test funkcji pomocniczej analyze_capacity."""
        carriers = self.get_test_carriers()

        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
            "width_mm": [80.0, 100.0],
            "height_mm": [50.0, 60.0],
            "weight_kg": [5.0, 10.0],
        })

        result = analyze_capacity(df, carriers)

        assert result.total_sku == 2
        assert len(result.df) > 0


# ============================================================================
# Testy ShiftSchedule
# ============================================================================


class TestShiftSchedule:
    """Testy dla ShiftSchedule."""

    def get_test_weekly_schedule(self) -> WeeklySchedule:
        """Pobierz testowy harmonogram tygodniowy."""
        return WeeklySchedule(
            timezone="Europe/Warsaw",
            productive_hours_per_shift=7.0,
            mon=[
                ShiftConfig(name="S1", start="07:00", end="15:00", shift_type=ShiftType.BASE),
                ShiftConfig(name="S2", start="15:00", end="23:00", shift_type=ShiftType.BASE),
            ],
            tue=[
                ShiftConfig(name="S1", start="07:00", end="15:00", shift_type=ShiftType.BASE),
            ],
            wed=[],
            thu=[],
            fri=[],
            sat=[],
            sun=[],
        )

    def test_get_shifts_for_date_monday(self):
        """Test pobierania zmian dla poniedzialku."""
        weekly = self.get_test_weekly_schedule()
        schedule = ShiftSchedule(weekly_schedule=weekly)

        # Poniedzialek
        monday = date(2024, 10, 14)  # To jest poniedzialek
        shifts = schedule.get_shifts_for_date(monday)

        assert len(shifts) == 2
        assert shifts[0].name == "S1"
        assert shifts[1].name == "S2"

    def test_get_shifts_for_date_wednesday(self):
        """Test pobierania zmian dla srody (brak zmian)."""
        weekly = self.get_test_weekly_schedule()
        schedule = ShiftSchedule(weekly_schedule=weekly)

        wednesday = date(2024, 10, 16)
        shifts = schedule.get_shifts_for_date(wednesday)

        assert len(shifts) == 0

    def test_exception_range_overlay(self):
        """Test dodatkowych zmian z range_overlay."""
        weekly = self.get_test_weekly_schedule()
        exceptions = [
            {
                "id": "peak",
                "type": "range_overlay",
                "from": "2024-10-14",
                "to": "2024-10-20",
                "add_shifts_by_weekday": {
                    "Mon": [{"name": "OT", "start": "23:00", "end": "03:00", "shift_type": "overlay"}],
                }
            }
        ]
        schedule = ShiftSchedule(weekly_schedule=weekly, exceptions=exceptions)

        monday = date(2024, 10, 14)
        shifts = schedule.get_shifts_for_date(monday)

        # 2 base shifts + 1 overlay
        assert len(shifts) == 3
        assert any(s.name == "OT" for s in shifts)

    def test_calculate_total_hours(self):
        """Test obliczania calkowitych godzin."""
        weekly = self.get_test_weekly_schedule()
        schedule = ShiftSchedule(weekly_schedule=weekly)

        # Tydzien od poniedzialku do niedzieli
        start = date(2024, 10, 14)
        end = date(2024, 10, 20)

        total = schedule.calculate_total_hours(start, end)

        # Poniedzialek: 2 zmiany * 7h = 14h
        # Wtorek: 1 zmiana * 7h = 7h
        # Razem: 21h
        assert total == 21.0

    def test_load_from_file(self):
        """Test wczytywania harmonogramu z pliku."""
        schedule = load_shifts(FIXTURES_DIR / "shifts_base.yml")

        assert schedule.weekly_schedule is not None
        assert schedule.weekly_schedule.productive_hours_per_shift > 0


# ============================================================================
# Testy PerformanceAnalyzer
# ============================================================================


class TestPerformanceAnalyzer:
    """Testy dla PerformanceAnalyzer."""

    def get_test_orders(self) -> pl.DataFrame:
        """Pobierz testowe zamowienia."""
        return pl.DataFrame({
            "order_id": ["ORD1", "ORD1", "ORD2", "ORD3", "ORD3", "ORD3"],
            "sku": ["SKU1", "SKU2", "SKU1", "SKU1", "SKU2", "SKU3"],
            "quantity": [2, 3, 5, 1, 2, 4],
            "timestamp": [
                datetime(2024, 10, 15, 10, 30),
                datetime(2024, 10, 15, 10, 30),
                datetime(2024, 10, 15, 14, 45),
                datetime(2024, 10, 16, 9, 15),
                datetime(2024, 10, 16, 9, 15),
                datetime(2024, 10, 16, 9, 15),
            ],
        })

    def test_analyze_basic(self):
        """Test podstawowej analizy."""
        df = self.get_test_orders()
        analyzer = PerformanceAnalyzer()

        result = analyzer.analyze(df)

        assert result.kpi.total_lines == 6
        assert result.kpi.total_orders == 3
        assert result.kpi.total_units == 17
        assert result.kpi.unique_sku == 3

    def test_calculate_hourly_metrics(self):
        """Test obliczania metryk godzinowych."""
        df = self.get_test_orders()
        analyzer = PerformanceAnalyzer()

        hourly = analyzer._calculate_hourly_metrics(df)

        assert len(hourly) == 3  # 3 rozne godziny (9, 10, 14)
        hours = [h.hour for h in hourly]
        assert 9 in hours
        assert 10 in hours
        assert 14 in hours

    def test_calculate_daily_metrics(self):
        """Test obliczania metryk dziennych."""
        df = self.get_test_orders()
        analyzer = PerformanceAnalyzer()

        daily = analyzer._calculate_daily_metrics(df)

        assert len(daily) == 2  # 2 dni
        assert daily[0].date == date(2024, 10, 15)
        assert daily[1].date == date(2024, 10, 16)

    def test_calculate_kpi(self):
        """Test obliczania KPI."""
        df = self.get_test_orders()
        analyzer = PerformanceAnalyzer()

        hourly = analyzer._calculate_hourly_metrics(df)
        kpi = analyzer._calculate_kpi(df, hourly)

        assert kpi.avg_lines_per_order == 2.0  # 6 lines / 3 orders
        assert kpi.avg_units_per_line == 17 / 6
        assert kpi.peak_lines_per_hour > 0

    def test_analyze_with_shift_schedule(self):
        """Test analizy z harmonogramem zmian."""
        df = self.get_test_orders()

        # Utworz prosty harmonogram
        weekly = WeeklySchedule(
            productive_hours_per_shift=7.0,
            mon=[ShiftConfig(name="S1", start="07:00", end="15:00")],
            tue=[ShiftConfig(name="S1", start="07:00", end="15:00")],
            wed=[ShiftConfig(name="S1", start="07:00", end="15:00")],
            thu=[ShiftConfig(name="S1", start="07:00", end="15:00")],
            fri=[],
            sat=[],
            sun=[],
        )
        schedule = ShiftSchedule(weekly_schedule=weekly)

        analyzer = PerformanceAnalyzer(shift_schedule=schedule)
        result = analyzer.analyze(df)

        assert result.total_productive_hours > 0

    def test_analyze_performance_helper(self):
        """Test funkcji pomocniczej analyze_performance."""
        df = self.get_test_orders()
        result = analyze_performance(df)

        assert result.kpi is not None
        assert result.date_from == date(2024, 10, 15)
        assert result.date_to == date(2024, 10, 16)


# ============================================================================
# Testy integracyjne
# ============================================================================


class TestAnalyticsIntegration:
    """Testy integracyjne dla modulu analytics."""

    def test_capacity_with_fixtures(self):
        """Test analizy pojemnosciowej z fixtures."""
        import yaml

        # Wczytaj nosniki
        with open(FIXTURES_DIR / "carriers.yml", "r") as f:
            carriers_data = yaml.safe_load(f)

        carriers = [
            CarrierConfig(**c) for c in carriers_data["carriers"]
        ]

        # Wczytaj masterdata
        from src.ingest.readers import read_file
        md_df = read_file(FIXTURES_DIR / "masterdata_clean.csv")

        # Analizuj
        result = analyze_capacity(md_df, carriers)

        assert result.total_sku > 0
        assert result.fit_percentage > 0
        assert len(result.carriers_analyzed) == len(carriers)

    def test_performance_with_fixtures(self):
        """Test analizy wydajnosciowej z fixtures."""
        from src.ingest.readers import read_file
        from src.model.orders import OrdersProcessor

        # Wczytaj orders
        orders_df = read_file(FIXTURES_DIR / "orders_clean.csv")

        # Normalizuj (konwertuj timestamp)
        processor = OrdersProcessor()
        normalized = processor.normalize(orders_df)

        # Wczytaj harmonogram
        schedule = load_shifts(FIXTURES_DIR / "shifts_base.yml")

        # Analizuj
        result = analyze_performance(normalized, schedule)

        assert result.kpi.total_lines > 0
        assert result.kpi.total_orders > 0
        assert len(result.hourly_metrics) > 0
        assert len(result.daily_metrics) > 0
