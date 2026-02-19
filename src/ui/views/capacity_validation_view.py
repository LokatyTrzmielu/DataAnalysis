"""Capacity validation view - masterdata quality validation tab."""

from __future__ import annotations

import streamlit as st

from src.ui.layout import render_divider, render_forward_guidance, render_kpi_section, render_section_header
from src.ui.theme import COLORS


def render_capacity_validation_view(show_header: bool = True) -> None:
    """Render the Capacity Validation tab content.

    Args:
        show_header: Whether to display the header. Set to False when embedded in another view.
    """
    if show_header:
        st.header("✅ Validation")

    if st.session_state.masterdata_df is None:
        st.info("Import Masterdata in the Import tab first")
        return

    # Auto-run validation on first visit (consistent with Performance auto-validation)
    auto_run = st.session_state.quality_result is None

    if auto_run:
        with st.spinner("Validation in progress..."):
            try:
                from src.quality import run_quality_pipeline
                from src.quality.impute import ImputationMethod

                result = run_quality_pipeline(
                    st.session_state.masterdata_df,
                    enable_imputation=True,
                    imputation_method=ImputationMethod.MEDIAN,
                )
                st.session_state.quality_result = result
                st.session_state.masterdata_df = result.df
                st.rerun()

            except Exception as e:
                st.error(f"Validation error: {e}")

    # Display results
    if st.session_state.quality_result is not None:
        _render_capacity_validation_results()


def _render_capacity_validation_results() -> None:
    """Display capacity validation results."""
    result = st.session_state.quality_result

    render_section_header("Masterdata summary", "📋")
    metrics = [
        {
            "title": "Quality Score",
            "value": f"{result.quality_score:.1f}%",
            "help_text": (
                "Weighted average of data coverage: dimensions (40%), weight (30%), "
                "stock (30%), minus penalty for detected issues (0.5 point per issue, max 30). "
                "Higher score indicates better data quality."
            ),
        },
        {"title": "Records", "value": result.total_records, "help_text": "Total SKU records"},
        {"title": "Valid", "value": result.valid_records, "help_text": "Records with complete data"},
        {
            "title": "Imputed",
            "value": result.imputed_records,
            "help_text": "Records with missing values filled using the median of each field across the dataset.",
        },
    ]
    render_kpi_section(metrics)
    render_divider()

    # Coverage comparison table
    render_section_header("Data coverage", "📊")

    def _coverage_color(pct: float) -> str:
        if pct >= 100:
            return COLORS["primary"]
        if pct >= 90:
            return COLORS["accent"]
        return COLORS["error"]

    def _delta_color(delta: float) -> str:
        return COLORS["primary"] if delta > 0 else COLORS["info"]

    rows = [
        ("Dimensions", result.metrics_before.dimensions_coverage_pct, result.metrics_after.dimensions_coverage_pct),
        ("Weight", result.metrics_before.weight_coverage_pct, result.metrics_after.weight_coverage_pct),
    ]

    table_rows_html = ""
    for label, before, after in rows:
        delta = after - before
        delta_str = f"+{delta:.1f}pp" if delta > 0 else f"{delta:.1f}pp"
        table_rows_html += (
            f'<tr>'
            f'<td style="padding:0.5rem 0.75rem; color:{COLORS["text"]};">{label}</td>'
            f'<td style="padding:0.5rem 0.75rem; text-align:center; font-weight:600; color:{_coverage_color(before)};">{before:.1f}%</td>'
            f'<td style="padding:0.5rem 0.75rem; text-align:center; font-weight:600; color:{_coverage_color(after)};">{after:.1f}%</td>'
            f'<td style="padding:0.5rem 0.75rem; text-align:center; font-weight:600; color:{_delta_color(delta)};">{delta_str}</td>'
            f'</tr>'
        )

    header_style = f'background:{COLORS["surface_light"]}; padding:0.5rem 0.75rem; color:{COLORS["text_secondary"]}; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;'
    table_html = (
        f'<table style="width:100%; border-collapse:collapse; font-size:0.9rem;">'
        f'<thead><tr>'
        f'<th style="{header_style} text-align:left;">Metric</th>'
        f'<th style="{header_style} text-align:center;">Before</th>'
        f'<th style="{header_style} text-align:center;">After</th>'
        f'<th style="{header_style} text-align:center;">Delta</th>'
        f'</tr></thead>'
        f'<tbody>{table_rows_html}</tbody>'
        f'</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # Issues (Outliers and Borderline moved to Capacity Analysis)
    render_section_header("Detected issues", "⚠️")
    dq = result.dq_lists
    problems = {
        "Missing Critical": len(dq.missing_critical),
        "Duplicates": len(dq.duplicates),
        "Conflicts": len(dq.conflicts),
    }

    for name, count in problems.items():
        if count > 0:
            st.warning(f"{name}: {count}")
        else:
            st.success(f"{name}: 0")

    # Validation help section
    with st.expander("❓ Validation help", expanded=False):
        st.markdown("""
**Missing Critical** - Required fields (SKU, dimensions, weight) with missing or zero values.
These SKUs cannot be analyzed until the data is corrected.

**Duplicates** - Same SKU appearing multiple times in the masterdata.
Each SKU should appear only once with consistent dimension data.

**Conflicts** - Same SKU with different dimension or weight values across records.
Indicates inconsistent data that needs to be resolved.
        """)
