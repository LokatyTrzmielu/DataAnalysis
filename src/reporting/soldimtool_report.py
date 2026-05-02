"""SolDimTool Dashboard Input report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl

from src.analytics.performance import PerformanceAnalysisResult
from src.analytics.soldimtool_calculator import SolDimToolCalculator, SolDimToolInputs
from src.reporting.csv_writer import CSVWriter


class SolDimToolReportGenerator:
    """Generates SolDimTool v2.7.3 Dashboard Input report (CSV)."""

    def generate(
        self,
        output_path: Path,
        result: PerformanceAnalysisResult,
        source_file: str = "",
    ) -> Path:
        """Generate the report.

        Args:
            output_path: Destination path for the CSV file
            result: Completed PerformanceAnalysisResult
            source_file: Optional source file name for the report header

        Returns:
            Path to the generated file
        """
        inputs = SolDimToolCalculator().calculate(result)
        rows = self._build_rows(inputs, source_file)

        df = pl.DataFrame(
            {
                "Section": [r[0] for r in rows],
                "Cell": [r[1] for r in rows],
                "Metric": [r[2] for r in rows],
                "Value": [r[3] for r in rows],
                "Note": [r[4] for r in rows],
            }
        )

        return CSVWriter().write(df, output_path)

    # ------------------------------------------------------------------

    def _build_rows(
        self, inp: SolDimToolInputs, source_file: str
    ) -> list[tuple[str, str, str, str, str]]:
        rows: list[tuple[str, str, str, str, str]] = []

        # --- Info header ---
        rows.append(
            ("Info", "", "Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "")
        )
        if source_file:
            rows.append(("Info", "", "Source file", source_file, ""))

        # --- Order Information ---
        rows.append(
            ("Order Information", "C16", "Orders/Day - Mean", str(inp.orders_per_day_mean), "")
        )
        rows.append(
            ("Order Information", "C16", "Orders/Day - Median", str(inp.orders_per_day_median), "")
        )
        rows.append(
            ("Order Information", "C16", "Orders/Day - P90", str(inp.orders_per_day_p90), "")
        )
        rows.append(
            (
                "Order Information",
                "C16",
                "Orders/Day - Recommended",
                str(inp.orders_per_day_recommended),
                f"Basis: {inp.orders_recommended_basis} — enter in C16",
            )
        )
        rows.append(
            ("Order Information", "C17", "Orderlines/Order - Mean", str(inp.ol_per_order_mean), "")
        )
        rows.append(
            (
                "Order Information",
                "C17",
                "Orderlines/Order - Median",
                str(inp.ol_per_order_median),
                "",
            )
        )
        rows.append(
            ("Order Information", "C17", "Orderlines/Order - P90", str(inp.ol_per_order_p90), "")
        )
        rows.append(
            (
                "Order Information",
                "C17",
                "Orderlines/Order - Recommended",
                str(inp.ol_per_order_recommended),
                "enter in C17",
            )
        )

        # --- Station Based: Orders/Batch ---
        rows.append(
            (
                "Station Based",
                "",
                "max_batch",
                str(inp.max_batch),
                f"floor({inp.orders_per_day_recommended} / 4), clamped to [5, 100]",
            )
        )
        for i, bs in enumerate(inp.batch_sizes, start=1):
            cell = f"B{20 + i}"
            rows.append(
                (
                    "Station Based",
                    cell,
                    f"Orders/Batch {i}.",
                    str(bs),
                    f"enter in {cell}",
                )
            )

        # --- Station Based: Commonality ---
        sku_note = (
            ""
            if inp.sku_available
            else "No SKU column — default range 0–20% applied. Adjust based on product knowledge."
        )
        if inp.sku_available and inp.base_commonality is not None:
            rows.append(
                (
                    "Station Based",
                    "",
                    "Commonality - empirical base",
                    str(inp.base_commonality),
                    "Empirical estimate from SKU data (500 sampled batches of 10 orders)",
                )
            )
        for i, cv in enumerate(inp.commonality_values, start=1):
            cell = f"C{20 + i}"
            rows.append(
                (
                    "Station Based",
                    cell,
                    f"Commonality {i}.",
                    str(cv),
                    sku_note if i == 1 else f"enter in {cell}",
                )
            )

        # --- Picking: Hours/Day ---
        rows.append(
            (
                "Picking",
                "A29",
                "time_detected",
                "YES" if inp.time_detected else "NO",
                "",
            )
        )
        if inp.window_min_hour is not None:
            rows.append(
                (
                    "Picking",
                    "A29",
                    "Operational window min hour",
                    str(int(inp.window_min_hour)),
                    "",
                )
            )
            rows.append(
                (
                    "Picking",
                    "A29",
                    "Operational window max hour",
                    str(int(inp.window_max_hour)),
                    "",
                )
            )
            rows.append(
                (
                    "Picking",
                    "A29",
                    "Operational window median (h)",
                    str(inp.window_median),
                    "",
                )
            )
        else:
            rows.append(
                (
                    "Picking",
                    "A29",
                    "Hours/Day fallback reason",
                    "No time data — default value of 8h applied. Verify manually.",
                    "",
                )
            )
        rows.append(
            (
                "Picking",
                "A29",
                "Hours/Day - Recommended",
                str(inp.hours_per_day),
                "enter in A29",
            )
        )

        # --- Picking: Adjusting View ---
        adj_reason = (
            "hours/day <= 8" if inp.adjusting_view == "hourly view" else "hours/day > 8"
        )
        rows.append(
            (
                "Picking",
                "A31",
                "Adjusting View - Recommended",
                inp.adjusting_view,
                f"Reason: {adj_reason} — enter in A31",
            )
        )

        # --- Picking: System Factor ---
        rows.append(
            (
                "Picking",
                "C29",
                "System Factor - Recommended",
                str(inp.system_factor),
                "Default value 10%. Adjust manually based on machine service data. — enter in C29",
            )
        )

        # --- Warnings ---
        if inp.warnings:
            for w in inp.warnings:
                rows.append(("Warnings", "", "", w, ""))
        else:
            rows.append(("Warnings", "", "", "none", ""))

        return rows
