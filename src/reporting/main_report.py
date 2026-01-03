"""Generowanie glownego raportu Report_Main.csv."""

from pathlib import Path
from typing import Optional

from src.core.formatting import Formatter
from src.quality.pipeline import QualityPipelineResult
from src.analytics.capacity import CapacityAnalysisResult
from src.analytics.performance import PerformanceAnalysisResult
from src.reporting.csv_writer import CSVWriter


class MainReportGenerator:
    """Generator glownego raportu."""

    def __init__(self) -> None:
        """Inicjalizacja generatora."""
        self.formatter = Formatter()
        self.writer = CSVWriter()

    def generate(
        self,
        output_path: Path,
        quality_result: Optional[QualityPipelineResult] = None,
        capacity_result: Optional[CapacityAnalysisResult] = None,
        performance_result: Optional[PerformanceAnalysisResult] = None,
        client_name: str = "",
    ) -> Path:
        """Generuj glowny raport.

        Args:
            output_path: Sciezka do pliku wynikowego
            quality_result: Wyniki jakosci danych
            capacity_result: Wyniki analizy pojemnosciowej
            performance_result: Wyniki analizy wydajnosciowej
            client_name: Nazwa klienta

        Returns:
            Sciezka do wygenerowanego pliku
        """
        data: list[tuple[str, str, str]] = []

        # Sekcja: Info
        data.append(("Info", "Client", client_name))
        data.append(("Info", "Generated", Formatter.datetime_iso(__import__("datetime").datetime.now())))

        # Sekcja: Data Quality
        if quality_result:
            self._add_quality_section(data, quality_result)

        # Sekcja: Capacity
        if capacity_result:
            self._add_capacity_section(data, capacity_result)

        # Sekcja: Performance
        if performance_result:
            self._add_performance_section(data, performance_result)

        return self.writer.write_key_value(data, output_path)

    def _add_quality_section(
        self,
        data: list[tuple[str, str, str]],
        result: QualityPipelineResult,
    ) -> None:
        """Dodaj sekcje Data Quality."""
        data.append(("Data Quality", "Total Records", Formatter.integer(result.total_records)))
        data.append(("Data Quality", "Valid Records", Formatter.integer(result.valid_records)))
        data.append(("Data Quality", "Quality Score", Formatter.percent(result.quality_score)))

        # Coverage
        data.append(("Data Quality", "Dimensions Coverage Before", Formatter.percent(result.metrics_before.dimensions_coverage_pct)))
        data.append(("Data Quality", "Dimensions Coverage After", Formatter.percent(result.metrics_after.dimensions_coverage_pct)))
        data.append(("Data Quality", "Weight Coverage Before", Formatter.percent(result.metrics_before.weight_coverage_pct)))
        data.append(("Data Quality", "Weight Coverage After", Formatter.percent(result.metrics_after.weight_coverage_pct)))

        # Imputacja
        if result.imputation:
            data.append(("Data Quality", "Imputed Values", Formatter.integer(result.imputation.total_imputed)))
            data.append(("Data Quality", "Imputation Rate", Formatter.percent(result.imputation.imputation_rate)))

        # Problemy
        data.append(("Data Quality", "Total DQ Issues", Formatter.integer(result.dq_lists.total_issues)))
        data.append(("Data Quality", "Missing Critical", Formatter.integer(len(result.dq_lists.missing_critical))))
        data.append(("Data Quality", "Suspect Outliers", Formatter.integer(len(result.dq_lists.suspect_outliers))))
        data.append(("Data Quality", "Duplicates", Formatter.integer(len(result.dq_lists.duplicates))))

    def _add_capacity_section(
        self,
        data: list[tuple[str, str, str]],
        result: CapacityAnalysisResult,
    ) -> None:
        """Dodaj sekcje Capacity."""
        data.append(("Capacity", "Total SKU Analyzed", Formatter.integer(result.total_sku)))
        data.append(("Capacity", "Carriers Analyzed", ", ".join(result.carriers_analyzed)))
        data.append(("Capacity", "FIT Count", Formatter.integer(result.fit_count)))
        data.append(("Capacity", "BORDERLINE Count", Formatter.integer(result.borderline_count)))
        data.append(("Capacity", "NOT_FIT Count", Formatter.integer(result.not_fit_count)))
        data.append(("Capacity", "Fit Percentage", Formatter.percent(result.fit_percentage)))

    def _add_performance_section(
        self,
        data: list[tuple[str, str, str]],
        result: PerformanceAnalysisResult,
    ) -> None:
        """Dodaj sekcje Performance."""
        kpi = result.kpi

        # Totals
        data.append(("Performance", "Total Lines", Formatter.integer(kpi.total_lines)))
        data.append(("Performance", "Total Orders", Formatter.integer(kpi.total_orders)))
        data.append(("Performance", "Total Units", Formatter.integer(kpi.total_units)))
        data.append(("Performance", "Unique SKU", Formatter.integer(kpi.unique_sku)))

        # Date range
        data.append(("Performance", "Date From", str(result.date_from)))
        data.append(("Performance", "Date To", str(result.date_to)))
        data.append(("Performance", "Total Productive Hours", Formatter.rate(result.total_productive_hours)))

        # Averages
        data.append(("Performance", "Avg Lines/Hour", Formatter.rate(kpi.avg_lines_per_hour)))
        data.append(("Performance", "Avg Orders/Hour", Formatter.rate(kpi.avg_orders_per_hour)))
        data.append(("Performance", "Avg Units/Hour", Formatter.rate(kpi.avg_units_per_hour)))

        # Per order/line
        data.append(("Performance", "Avg Lines/Order", Formatter.average(kpi.avg_lines_per_order)))
        data.append(("Performance", "Avg Units/Line", Formatter.average(kpi.avg_units_per_line)))
        data.append(("Performance", "Avg Units/Order", Formatter.average(kpi.avg_units_per_order)))

        # Peaks
        data.append(("Performance", "Peak Lines/Hour", Formatter.integer(kpi.peak_lines_per_hour)))
        data.append(("Performance", "Peak Orders/Hour", Formatter.integer(kpi.peak_orders_per_hour)))

        # Percentiles
        data.append(("Performance", "P90 Lines/Hour", Formatter.rate(kpi.p90_lines_per_hour)))
        data.append(("Performance", "P95 Lines/Hour", Formatter.rate(kpi.p95_lines_per_hour)))

        # Shift performance
        for sp in result.shift_performance:
            prefix = f"Performance ({sp.shift_type})"
            data.append((prefix, "Total Hours", Formatter.rate(sp.total_hours)))
            data.append((prefix, "Lines/Hour", Formatter.rate(sp.lines_per_hour)))
            data.append((prefix, "% of Work", Formatter.percent(sp.percentage_of_work)))


def generate_main_report(
    output_path: Path,
    **kwargs,
) -> Path:
    """Funkcja pomocnicza do generowania glownego raportu.

    Args:
        output_path: Sciezka do pliku wynikowego
        **kwargs: Argumenty dla MainReportGenerator.generate()

    Returns:
        Sciezka do wygenerowanego pliku
    """
    generator = MainReportGenerator()
    return generator.generate(output_path, **kwargs)
