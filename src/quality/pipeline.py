"""Pipeline jakosci danych - integracja walidacji, metryk i imputacji."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.quality.validators import MasterdataValidator, ValidationResult
from src.quality.dq_metrics import DataQualityCalculator, DataQualityMetrics
from src.quality.dq_lists import DQListBuilder, DQLists
from src.quality.impute import Imputer, ImputationResult, ImputationMethod


@dataclass
class QualityPipelineResult:
    """Wynik pipeline jakosci danych."""
    df: pl.DataFrame
    validation: ValidationResult
    metrics_before: DataQualityMetrics
    metrics_after: DataQualityMetrics
    dq_lists: DQLists
    imputation: Optional[ImputationResult] = None
    total_records: int = 0
    valid_records: int = 0
    imputed_records: int = 0

    @property
    def quality_score(self) -> float:
        """Ogolny wynik jakosci (0-100)."""
        # Srednia wazona metryk pokrycia
        coverage = (
            self.metrics_after.dimensions_coverage_pct * 0.4 +
            self.metrics_after.weight_coverage_pct * 0.3 +
            self.metrics_after.stock_coverage_pct * 0.3
        )
        # Kara za problemy
        penalty = min(30, self.dq_lists.total_issues * 0.5)
        return max(0, coverage - penalty)


class QualityPipeline:
    """Pipeline jakosci danych dla Masterdata."""

    def __init__(
        self,
        enable_imputation: bool = True,
        imputation_method: ImputationMethod = ImputationMethod.MEDIAN,
        treat_zero_as_missing: bool = True,
        treat_negative_as_missing: bool = True,
    ) -> None:
        """Inicjalizacja pipeline.

        Args:
            enable_imputation: Czy wykonac imputacje
            imputation_method: Metoda imputacji
            treat_zero_as_missing: Czy traktowac 0 jako brak
            treat_negative_as_missing: Czy traktowac ujemne jako brak
        """
        self.enable_imputation = enable_imputation
        self.imputation_method = imputation_method

        self.validator = MasterdataValidator(
            treat_zero_as_missing_dimensions=treat_zero_as_missing,
            treat_zero_as_missing_weight=treat_zero_as_missing,
            treat_negative_as_missing=treat_negative_as_missing,
        )
        self.metrics_calculator = DataQualityCalculator(
            treat_zero_as_missing=treat_zero_as_missing,
            treat_negative_as_missing=treat_negative_as_missing,
        )
        self.dq_list_builder = DQListBuilder()
        self.imputer = Imputer(
            method=imputation_method,
            treat_zero_as_missing=treat_zero_as_missing,
        )

    def run(
        self,
        df: pl.DataFrame,
        carrier_limits: Optional[dict[str, float]] = None,
    ) -> QualityPipelineResult:
        """Uruchom pipeline jakosci danych.

        Args:
            df: DataFrame z danymi Masterdata
            carrier_limits: Limity nosnikow dla borderline analysis

        Returns:
            QualityPipelineResult z wynikami
        """
        # 1. Walidacja
        validation = self.validator.validate(df)
        df_validated = validation.df_validated

        # 2. Metryki przed imputacja
        metrics_before = self.metrics_calculator.calculate(df_validated)

        # 3. Imputacja (opcjonalna)
        imputation = None
        df_imputed = df_validated

        if self.enable_imputation:
            imputation = self.imputer.impute(df_validated)
            df_imputed = imputation.df

        # 4. Metryki po imputacji
        metrics_after = self.metrics_calculator.calculate(df_imputed)

        # 5. Listy DQ
        dq_lists = self.dq_list_builder.build_all_lists(df_imputed, carrier_limits)

        # Podsumowanie
        total_records = len(df)
        valid_records = validation.valid_records
        imputed_records = imputation.total_imputed if imputation else 0

        return QualityPipelineResult(
            df=df_imputed,
            validation=validation,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            dq_lists=dq_lists,
            imputation=imputation,
            total_records=total_records,
            valid_records=valid_records,
            imputed_records=imputed_records,
        )


def run_quality_pipeline(
    df: pl.DataFrame,
    enable_imputation: bool = True,
    **kwargs,
) -> QualityPipelineResult:
    """Funkcja pomocnicza do uruchomienia pipeline jakosci.

    Args:
        df: DataFrame z danymi Masterdata
        enable_imputation: Czy wykonac imputacje
        **kwargs: Dodatkowe argumenty dla QualityPipeline

    Returns:
        QualityPipelineResult
    """
    pipeline = QualityPipeline(enable_imputation=enable_imputation, **kwargs)
    return pipeline.run(df)
