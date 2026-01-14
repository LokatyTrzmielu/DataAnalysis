"""Testy jednostkowe dla modulu quality."""

from pathlib import Path

import polars as pl
import pytest

from src.quality.validators import (
    MasterdataValidator,
    ValidationSeverity,
    ValidationIssueType,
)
from src.quality.dq_metrics import (
    DataQualityCalculator,
    FieldCoverage,
    calculate_dq_metrics,
)
from src.quality.dq_lists import DQListBuilder, build_dq_lists
from src.quality.impute import Imputer, ImputationMethod, impute_missing
from src.core.types import DataQualityFlag


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Testy MasterdataValidator
# ============================================================================


class TestMasterdataValidator:
    """Testy dla MasterdataValidator."""

    def test_validate_clean_data(self):
        """Test walidacji czystych danych."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
            "stock_qty": [10, 20, 30],
        })

        validator = MasterdataValidator()
        result = validator.validate(df)

        assert result.is_valid
        assert result.critical_issues == 0
        assert result.total_records == 3

    def test_validate_missing_null(self):
        """Test walidacji brakow NULL."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        validator = MasterdataValidator()
        result = validator.validate(df)

        assert result.warning_issues > 0
        missing_issues = [i for i in result.issues if i.issue_type == ValidationIssueType.MISSING_VALUE]
        assert len(missing_issues) == 1
        assert missing_issues[0].field == "length_mm"

    def test_validate_zeros_as_missing(self):
        """Test walidacji zer jako brakow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 0.0],
            "width_mm": [50.0, 100.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 0.0],
        })

        validator = MasterdataValidator(
            treat_zero_as_missing_dimensions=True,
            treat_zero_as_missing_weight=True,
        )
        result = validator.validate(df)

        zero_issues = [i for i in result.issues if i.issue_type == ValidationIssueType.ZERO_VALUE]
        assert len(zero_issues) == 2  # length i weight

    def test_validate_negative_values(self):
        """Test walidacji wartosci ujemnych."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, -50.0],
            "width_mm": [50.0, 100.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 3.0],
        })

        validator = MasterdataValidator(treat_negative_as_missing=True)
        result = validator.validate(df)

        negative_issues = [i for i in result.issues if i.issue_type == ValidationIssueType.NEGATIVE_VALUE]
        assert len(negative_issues) == 1
        assert negative_issues[0].original_value == "-50.0"

    def test_validate_outliers(self):
        """Test walidacji outlierow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 5000.0],  # 5000 jest outlierem
            "width_mm": [50.0, 100.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 3.0],
        })

        validator = MasterdataValidator()
        result = validator.validate(df)

        outlier_issues = [i for i in result.issues if i.issue_type == ValidationIssueType.OUTLIER]
        assert len(outlier_issues) == 1
        assert outlier_issues[0].field == "length_mm"

    def test_mark_as_missing_zero(self):
        """Test zamiany zer na NULL."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 0.0],
            "width_mm": [50.0, 0.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 0.0],
        })

        validator = MasterdataValidator()
        result = validator.validate(df)

        # Sprawdz czy zera zostaly zamienione na NULL
        assert result.df_validated["length_mm"][1] is None
        assert result.df_validated["width_mm"][1] is None
        assert result.df_validated["weight_kg"][1] is None


# ============================================================================
# Testy DataQualityCalculator
# ============================================================================


class TestDataQualityCalculator:
    """Testy dla DataQualityCalculator."""

    def test_calculate_full_coverage(self):
        """Test obliczania pelnego pokrycia."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
            "stock_qty": [10, 20, 30],
        })

        calculator = DataQualityCalculator()
        metrics = calculator.calculate(df)

        assert metrics.total_records == 3
        assert metrics.dimensions_coverage_pct == 100.0
        assert metrics.weight_coverage_pct == 100.0
        assert metrics.stock_coverage_pct == 100.0
        assert metrics.complete_records == 3
        assert metrics.partial_records == 0

    def test_calculate_partial_coverage(self):
        """Test obliczania czesciowego pokrycia."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 300.0],
            "width_mm": [50.0, 100.0, None],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 0.0, 4.5],  # 0 traktowane jako brak
        })

        calculator = DataQualityCalculator(treat_zero_as_missing=True)
        metrics = calculator.calculate(df)

        assert metrics.length_coverage.valid_count == 2
        assert metrics.width_coverage.valid_count == 2
        assert metrics.weight_coverage.valid_count == 2
        assert metrics.dimensions_coverage_pct < 100.0

    def test_calculate_field_coverage(self):
        """Test obliczania pokrycia pojedynczego pola."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4"],
            "length_mm": [100.0, 0.0, None, -50.0],
        })

        calculator = DataQualityCalculator(
            treat_zero_as_missing=True,
            treat_negative_as_missing=True,
        )
        coverage = calculator._calculate_field_coverage(df, "length_mm")

        assert coverage.total_records == 4
        assert coverage.null_count == 1
        assert coverage.zero_count == 1
        assert coverage.negative_count == 1
        assert coverage.valid_count == 1
        assert coverage.coverage_pct == 25.0

    def test_calculate_unique_sku(self):
        """Test liczenia unikalnych SKU."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU1", "SKU3"],  # SKU1 duplikat
            "length_mm": [100.0, 200.0, 300.0, 400.0],
            "width_mm": [50.0, 100.0, 150.0, 200.0],
            "height_mm": [30.0, 60.0, 90.0, 120.0],
            "weight_kg": [1.5, 3.0, 4.5, 6.0],
        })

        metrics = calculate_dq_metrics(df)
        assert metrics.unique_sku_count == 3

    def test_to_scorecard(self):
        """Test konwersji do DQScorecard."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2"],
            "length_mm": [100.0, 200.0],
            "width_mm": [50.0, 100.0],
            "height_mm": [30.0, 60.0],
            "weight_kg": [1.5, 3.0],
        })

        metrics = calculate_dq_metrics(df)
        scorecard = metrics.to_scorecard()

        assert scorecard.total_records == 2
        assert scorecard.dimensions_coverage_pct == 100.0


# ============================================================================
# Testy DQListBuilder
# ============================================================================


class TestDQListBuilder:
    """Testy dla DQListBuilder."""

    def test_find_missing_critical(self):
        """Test znajdowania brakujacych krytycznych danych."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 0.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        builder = DQListBuilder()
        missing = builder._find_missing_critical(df)

        assert len(missing) == 2  # NULL i 0
        skus = [item.sku for item in missing]
        assert "SKU2" in skus
        assert "SKU3" in skus

    def test_find_suspect_outliers(self):
        """Test znajdowania outlierow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 0.005, 4000.0],  # 0.005 < 0.01 (too small), 4000 > 3650 (too large)
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        builder = DQListBuilder()
        outliers = builder._find_suspect_outliers(df)

        assert len(outliers) == 2
        skus = [item.sku for item in outliers]
        assert "SKU2" in skus
        assert "SKU3" in skus

    def test_find_high_risk_borderline(self):
        """Test znajdowania SKU blisko limitow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 599.0, 600.0],  # 599 jest borderline przy limicie 600
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        builder = DQListBuilder(borderline_threshold_mm=2.0)
        carrier_limits = {"length_mm": 600.0}
        borderline = builder._find_high_risk_borderline(df, carrier_limits)

        assert len(borderline) == 2  # 599 i 600
        skus = [item.sku for item in borderline]
        assert "SKU2" in skus
        assert "SKU3" in skus

    def test_find_duplicates(self):
        """Test znajdowania duplikatow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU1", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0, 400.0],
        })

        builder = DQListBuilder()
        duplicates = builder._find_duplicates(df)

        assert len(duplicates) == 1
        assert duplicates[0].sku == "SKU1"
        assert duplicates[0].value == "2"

    def test_find_conflicts(self):
        """Test znajdowania konfliktow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU1", "SKU2"],
            "length_mm": [100.0, 150.0, 200.0],  # SKU1 ma rozne wartosci
            "width_mm": [50.0, 50.0, 100.0],
            "height_mm": [30.0, 30.0, 60.0],
            "weight_kg": [1.5, 1.5, 3.0],
        })

        builder = DQListBuilder()
        conflicts = builder._find_conflicts(df)

        assert len(conflicts) == 1
        assert conflicts[0].sku == "SKU1"
        assert conflicts[0].field == "length_mm"

    def test_build_all_lists(self):
        """Test budowania wszystkich list."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 300.0],
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        lists = build_dq_lists(df)

        assert lists.total_issues > 0
        assert len(lists.missing_critical) > 0

    def test_outlier_detection_disabled(self):
        """Test that outliers are not detected when flag is False."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 0.005, 4000.0],  # 0.005 < 0.01 (too small), 4000 > 3650 (too large)
            "width_mm": [50.0, 100.0, 150.0],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, 3.0, 4.5],
        })

        # With outlier detection enabled (default)
        builder_enabled = DQListBuilder(enable_outlier_detection=True)
        outliers_enabled = builder_enabled._find_suspect_outliers(df)
        assert len(outliers_enabled) == 2  # Should find 2 outliers

        # With outlier detection disabled
        builder_disabled = DQListBuilder(enable_outlier_detection=False)
        outliers_disabled = builder_disabled._find_suspect_outliers(df)
        assert len(outliers_disabled) == 0  # Should find no outliers


# ============================================================================
# Testy Imputer
# ============================================================================


class TestImputer:
    """Testy dla Imputer."""

    def test_impute_median(self):
        """Test imputacji mediana."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4", "SKU5"],
            "length_mm": [100.0, 200.0, None, 400.0, 500.0],
        })

        imputer = Imputer(method=ImputationMethod.MEDIAN)
        result = imputer.impute(df, fields=["length_mm"])

        # Mediana z [100, 200, 400, 500] = 300
        assert result.df["length_mm"][2] == 300.0
        assert result.total_imputed == 1

    def test_impute_mean(self):
        """Test imputacji srednia."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4"],
            "length_mm": [100.0, 200.0, 300.0, None],
        })

        imputer = Imputer(method=ImputationMethod.MEAN)
        result = imputer.impute(df, fields=["length_mm"])

        # Srednia z [100, 200, 300] = 200
        assert result.df["length_mm"][3] == 200.0

    def test_impute_zero_as_missing(self):
        """Test imputacji zer."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 0.0, 300.0],
        })

        imputer = Imputer(treat_zero_as_missing=True)
        result = imputer.impute(df, fields=["length_mm"])

        # 0 powinno zostac zastapione mediana z [100, 300] = 200
        assert result.df["length_mm"][1] == 200.0
        assert result.total_imputed == 1

    def test_impute_adds_flag(self):
        """Test dodawania flagi ESTIMATED."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 300.0],
        })

        imputer = Imputer()
        result = imputer.impute(df, fields=["length_mm"])

        # Sprawdz flage
        assert "length_flag" in result.df.columns
        flags = result.df["length_flag"].to_list()
        assert flags[0] == DataQualityFlag.RAW.value
        assert flags[1] == DataQualityFlag.ESTIMATED.value
        assert flags[2] == DataQualityFlag.RAW.value

    def test_impute_multiple_fields(self):
        """Test imputacji wielu pol."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, None, 300.0],
            "width_mm": [50.0, 100.0, None],
            "height_mm": [30.0, 60.0, 90.0],
            "weight_kg": [1.5, None, 4.5],
        })

        imputer = Imputer()
        result = imputer.impute(df)

        # Wszystkie braki powinny byc uzupelnione
        assert result.df["length_mm"].null_count() == 0
        assert result.df["width_mm"].null_count() == 0
        assert result.df["weight_kg"].null_count() == 0
        assert result.total_imputed == 3

    def test_impute_stats(self):
        """Test statystyk imputacji."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4"],
            "length_mm": [100.0, None, None, 400.0],
        })

        imputer = Imputer()
        result = imputer.impute(df, fields=["length_mm"])

        assert len(result.stats) == 1
        stat = result.stats[0]
        assert stat.field_name == "length_mm"
        assert stat.original_missing == 2
        assert stat.imputed_count == 2
        assert stat.method == ImputationMethod.MEDIAN

    def test_imputation_rate(self):
        """Test obliczania wskaznika imputacji."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4"],
            "length_mm": [100.0, None, None, 400.0],
        })

        result = impute_missing(df, fields=["length_mm"])

        assert result.total_records == 4
        assert result.total_imputed == 2
        assert result.imputation_rate == 50.0

    def test_impute_no_missing(self):
        """Test imputacji gdy brak brakow."""
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3"],
            "length_mm": [100.0, 200.0, 300.0],
        })

        imputer = Imputer()
        result = imputer.impute(df, fields=["length_mm"])

        assert result.total_imputed == 0
        assert len(result.stats) == 0


# ============================================================================
# Testy integracyjne
# ============================================================================


class TestQualityIntegration:
    """Testy integracyjne dla modulu quality."""

    def test_full_quality_pipeline(self):
        """Test pelnego pipeline'u jakosci."""
        # Dane z problemami
        df = pl.DataFrame({
            "sku": ["SKU1", "SKU2", "SKU3", "SKU4", "SKU1"],
            "length_mm": [100.0, 0.0, None, 5000.0, 100.0],  # duplikat SKU1
            "width_mm": [50.0, 100.0, 150.0, 200.0, 50.0],
            "height_mm": [30.0, 60.0, 90.0, 120.0, 30.0],
            "weight_kg": [1.5, 3.0, -4.5, 6.0, 1.5],  # ujemna waga
            "stock_qty": [10, 20, 30, 40, 10],
        })

        # 1. Walidacja
        validator = MasterdataValidator()
        validation_result = validator.validate(df)
        assert len(validation_result.issues) > 0

        # 2. Metryki
        metrics = calculate_dq_metrics(validation_result.df_validated)
        assert metrics.dimensions_coverage_pct < 100.0

        # 3. Listy DQ
        lists = build_dq_lists(validation_result.df_validated)
        assert lists.total_issues > 0
        assert len(lists.duplicates) > 0

        # 4. Imputacja
        imputation_result = impute_missing(validation_result.df_validated)
        assert imputation_result.total_imputed > 0

        # Po imputacji - brak NULL w wymiarach
        final_df = imputation_result.df
        assert final_df["length_mm"].null_count() == 0
