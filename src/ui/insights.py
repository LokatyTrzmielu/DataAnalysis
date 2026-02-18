"""Insight generation for analysis results.

Auto-generates key findings from capacity and performance analysis data.
Each insight has a type (positive/warning/info) and a message.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from src.ui.layout import render_section_header
from src.ui.theme import COLORS, STATUS_COLORS


@dataclass
class Insight:
    """A single insight / key finding."""
    message: str
    type: Literal["positive", "warning", "info"]


def generate_capacity_insights() -> list[Insight]:
    """Generate insights from capacity analysis result.

    Returns:
        List of Insight objects sorted by importance (warnings first).
    """
    result = st.session_state.get("capacity_result")
    if result is None:
        return []

    insights: list[Insight] = []

    # 1. Overall fit rate
    fit_rates = []
    for cid, stats in result.carrier_stats.items():
        if cid != "NONE":
            fit_rates.append(stats.fit_percentage)

    if fit_rates:
        avg_fit = sum(fit_rates) / len(fit_rates)
        if avg_fit >= 90:
            insights.append(Insight(
                f"Excellent carrier fit: {avg_fit:.0f}% of SKU fit on average across carriers.",
                "positive",
            ))
        elif avg_fit >= 70:
            insights.append(Insight(
                f"Good carrier fit: {avg_fit:.0f}% average fit rate across carriers.",
                "positive",
            ))
        else:
            insights.append(Insight(
                f"Low carrier fit: only {avg_fit:.0f}% average fit rate. "
                "Review carrier selection or SKU dimensions.",
                "warning",
            ))

    # 2. Best and worst carrier
    if len(fit_rates) > 1:
        best_cid, best_stats = max(
            ((cid, s) for cid, s in result.carrier_stats.items() if cid != "NONE"),
            key=lambda x: x[1].fit_percentage,
        )
        worst_cid, worst_stats = min(
            ((cid, s) for cid, s in result.carrier_stats.items() if cid != "NONE"),
            key=lambda x: x[1].fit_percentage,
        )
        if best_stats.fit_percentage != worst_stats.fit_percentage:
            insights.append(Insight(
                f"Best carrier: {best_stats.carrier_name} ({best_stats.fit_percentage:.0f}% fit). "
                f"Worst: {worst_stats.carrier_name} ({worst_stats.fit_percentage:.0f}% fit).",
                "info",
            ))

    # 3. Not-fit SKU (prioritized/best-fit mode)
    none_stats = result.carrier_stats.get("NONE")
    if none_stats and none_stats.not_fit_count > 0:
        pct = none_stats.not_fit_count / result.total_sku * 100
        insights.append(Insight(
            f"{none_stats.not_fit_count} SKU ({pct:.0f}%) don't fit any carrier — "
            "consider adding larger carriers or reviewing outlier dimensions.",
            "warning",
        ))

    # 4. Borderline SKU
    total_borderline = sum(
        s.borderline_count for cid, s in result.carrier_stats.items() if cid != "NONE"
    )
    if total_borderline > 0 and result.total_sku > 0:
        bl_pct = total_borderline / result.total_sku * 100
        if bl_pct > 15:
            insights.append(Insight(
                f"{total_borderline} borderline SKU ({bl_pct:.0f}%) — close to carrier limits. "
                "These may cause fitting issues in practice.",
                "warning",
            ))
        else:
            insights.append(Insight(
                f"{total_borderline} borderline SKU ({bl_pct:.0f}%) near carrier limits.",
                "info",
            ))

    # Sort: warnings first, then info, then positive
    priority = {"warning": 0, "info": 1, "positive": 2}
    insights.sort(key=lambda i: priority.get(i.type, 3))

    return insights


def generate_performance_insights() -> list[Insight]:
    """Generate insights from performance analysis result.

    Returns:
        List of Insight objects sorted by importance.
    """
    result = st.session_state.get("performance_result")
    if result is None:
        return []

    insights: list[Insight] = []
    kpi = result.kpi

    # 1. Volume summary
    insights.append(Insight(
        f"Analyzed {kpi.total_orders:,} orders with {kpi.total_lines:,} lines "
        f"across {kpi.unique_sku:,} unique SKU.",
        "info",
    ))

    # 2. Throughput variability
    if result.has_hourly_data and kpi.avg_lines_per_hour > 0:
        peak_ratio = kpi.p95_lines_per_hour / kpi.avg_lines_per_hour
        if peak_ratio > 3.0:
            insights.append(Insight(
                f"High throughput variability: P95 ({kpi.p95_lines_per_hour:.0f} lines/h) "
                f"is {peak_ratio:.1f}x the average ({kpi.avg_lines_per_hour:.0f} lines/h). "
                "Peak periods require significantly more capacity.",
                "warning",
            ))
        elif peak_ratio > 2.0:
            insights.append(Insight(
                f"Moderate throughput variability: P95 is {peak_ratio:.1f}x the average. "
                "Some peak buffering capacity recommended.",
                "info",
            ))
        else:
            insights.append(Insight(
                f"Stable throughput: P95 is only {peak_ratio:.1f}x the average — "
                "consistent workload pattern.",
                "positive",
            ))

    # 3. ABC analysis
    if result.sku_pareto:
        abc_a_count = sum(1 for s in result.sku_pareto if s.abc_class == "A")
        abc_a_lines = sum(s.total_lines for s in result.sku_pareto if s.abc_class == "A")
        total_lines = sum(s.total_lines for s in result.sku_pareto)
        if total_lines > 0:
            a_pct_sku = abc_a_count / len(result.sku_pareto) * 100
            a_pct_lines = abc_a_lines / total_lines * 100
            insights.append(Insight(
                f"ABC analysis: {abc_a_count} A-class SKU ({a_pct_sku:.0f}% of assortment) "
                f"generate {a_pct_lines:.0f}% of all order lines.",
                "info",
            ))

    # 4. Day-of-week pattern
    if result.weekday_profile:
        values = list(result.weekday_profile.values())
        if values:
            max_val = max(values)
            min_val = min(v for v in values if v > 0) if any(v > 0 for v in values) else 0
            if min_val > 0 and max_val / min_val > 2.0:
                day_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
                busiest_day = max(result.weekday_profile, key=result.weekday_profile.get)
                insights.append(Insight(
                    f"Uneven weekly pattern: busiest day ({day_names.get(busiest_day, '?')}) has "
                    f"{max_val / min_val:.1f}x more lines than the quietest day.",
                    "info",
                ))

    # 5. Order complexity
    if kpi.avg_lines_per_order > 5:
        insights.append(Insight(
            f"Complex orders: average {kpi.avg_lines_per_order:.1f} lines per order — "
            "consider multi-zone picking optimization.",
            "info",
        ))
    elif kpi.avg_lines_per_order < 1.5:
        insights.append(Insight(
            f"Simple orders: average {kpi.avg_lines_per_order:.1f} lines per order — "
            "single-pick optimization applicable.",
            "positive",
        ))

    # Sort: warnings first
    priority = {"warning": 0, "info": 1, "positive": 2}
    insights.sort(key=lambda i: priority.get(i.type, 3))

    return insights


def generate_validation_insights(result) -> list[Insight]:
    """Generate insights from capacity validation result.

    Returns:
        List of Insight objects describing data quality findings.
    """
    insights: list[Insight] = []

    dim_after = result.metrics_after.dimensions_coverage_pct
    wgt_after = result.metrics_after.weight_coverage_pct
    dim_before = result.metrics_before.dimensions_coverage_pct
    wgt_before = result.metrics_before.weight_coverage_pct
    score = result.quality_score

    # Overall quality score
    if score >= 90:
        insights.append(Insight(f"Quality score {score:.1f}% — excellent data quality", "positive"))
    elif score >= 70:
        insights.append(Insight(f"Quality score {score:.1f}% — acceptable, some issues detected", "info"))
    else:
        insights.append(Insight(f"Quality score {score:.1f}% — significant data quality issues", "warning"))

    # Coverage after imputation
    if dim_after == 100 and wgt_after == 100:
        insights.append(Insight("All records complete after imputation (100% coverage)", "positive"))
    else:
        if dim_after < 100:
            insights.append(Insight(f"Dimensions coverage {dim_after:.1f}% — some records still incomplete", "warning"))
        if wgt_after < 100:
            insights.append(Insight(f"Weight coverage {wgt_after:.1f}% — some records still incomplete", "warning"))

    # Imputation gains
    if result.imputed_records > 0:
        dim_gained = dim_after - dim_before
        insights.append(Insight(
            f"{result.imputed_records} records imputed"
            + (f" — dimensions coverage improved by {dim_gained:.1f}pp" if dim_gained > 0 else ""),
            "info",
        ))

    # Issue counts
    dq = result.dq_lists
    if len(dq.missing_critical) > 0:
        insights.append(Insight(f"{len(dq.missing_critical)} records with missing critical fields — manual correction needed", "warning"))
    if len(dq.duplicates) > 0:
        insights.append(Insight(f"{len(dq.duplicates)} duplicate SKUs detected", "warning"))
    if len(dq.conflicts) > 0:
        insights.append(Insight(f"{len(dq.conflicts)} conflicting dimension records", "warning"))
    if len(dq.missing_critical) == 0 and len(dq.duplicates) == 0 and len(dq.conflicts) == 0:
        insights.append(Insight("No critical issues detected in masterdata", "positive"))

    return insights


def render_insights(insights: list[Insight], title: str = "Key Findings") -> None:
    """Render a list of insights as styled cards.

    Args:
        insights: List of Insight objects to display
        title: Section title
    """
    if not insights:
        return

    render_section_header(title, "💡")

    type_config = {
        "positive": {"icon": "✅", "border": COLORS["primary"], "bg": "#e8f5e9"},
        "warning": {"icon": "⚠️", "border": COLORS["warning"], "bg": "#fef3cd"},
        "info": {"icon": "ℹ️", "border": STATUS_COLORS["in_progress"], "bg": "#e8f0fe"},
    }

    html_parts = []
    for insight in insights:
        cfg = type_config.get(insight.type, type_config["info"])
        html_parts.append(
            f'<div style="border-left: 3px solid {cfg["border"]}; background: {cfg["bg"]}; '
            f'padding: 0.6rem 0.9rem; margin-bottom: 0.5rem; border-radius: 4px; '
            f'font-size: 0.9rem; color: {COLORS["text"]};">'
            f'{cfg["icon"]} {insight.message}</div>'
        )

    st.markdown("".join(html_parts), unsafe_allow_html=True)
