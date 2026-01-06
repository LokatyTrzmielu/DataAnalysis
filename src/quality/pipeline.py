"""Data quality pipeline - integration of validation, metrics and imputation."""

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

from src.quality.validators import MasterdataValidator, ValidationResult
from src.quality.dq_metrics import DataQualityCalculator, DataQualityMetrics
from src.quality.dq_lists import DQListBuilder, DQLists
from src.quality.impute import Imputer, ImputationResult, ImputationMethod


@dataclass
class QualityPipelineResult:
    """Data quality pipeline result."""
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
        """Overall quality score (0-100)."""
        # Weighted average of coverage metrics
        coverage = (
            self.metrics_after.dimensions_coverage_pct * 0.4 +
            self.metrics_after.weight_coverage_pct * 0.3 +
            self.metrics_after.stock_coverage_pct * 0.3
        )
        # Penalty for issues
        penalty = min(30, self.dq_lists.total_issues * 0.5)
        return max(0, coverage - penalty)


class QualityPipeline:
    """Data quality pipeline for Masterdata."""

    def __init__(
        self,
        enable_imputation: bool = True,
        imputation_method: ImputationMethod = ImputationMethod.MEDIAN,
        treat_zero_as_missing: bool = True,
        treat_negative_as_missing: bool = True,
    ) -> None:
        """Initialize pipeline.

        Args:
            enable_imputation: Whether to perform imputation
            imputation_method: Imputation method
            treat_zero_as_missing: Whether to treat 0 as missing
            treat_negative_as_missing: Whether to treat negative as missing
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
        """Run data quality pipeline.

        Args:
            df: DataFrame with Masterdata
            carrier_limits: Carrier limits for borderline analysis

        Returns:
            QualityPipelineResult with results
        """
        # 1. Validation
        validation = self.validator.validate(df)
        df_validated = validation.df_validated

        # 2. Metrics before imputation
        metrics_before = self.metrics_calculator.calculate(df_validated)

        # 3. Imputation (optional)
        imputation = None
        df_imputed = df_validated

        if self.enable_imputation:
            imputation = self.imputer.impute(df_validated)
            df_imputed = imputation.df

        # 4. Metrics after imputation
        metrics_after = self.metrics_calculator.calculate(df_imputed)

        # 5. DQ lists
        dq_lists = self.dq_list_builder.build_all_lists(df_imputed, carrier_limits)

        # Summary
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
    """Helper function to run quality pipeline.

    Args:
        df: DataFrame with Masterdata
        enable_imputation: Whether to perform imputation
        **kwargs: Additional arguments for QualityPipeline

    Returns:
        QualityPipelineResult
    """
    pipeline = QualityPipeline(enable_imputation=enable_imputation, **kwargs)
    return pipeline.run(df)
