"""Capacity validation view - masterdata quality validation tab."""

from __future__ import annotations

import streamlit as st

from src.ui.insights import generate_validation_insights, render_insights
from src.ui.layout import render_divider, render_forward_guidance, render_section_header
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
    manual_run = st.button("Re-run validation", key="run_validation", type="primary")
    auto_run = st.session_state.quality_result is None

    if manual_run or auto_run:
        with st.spinner("Validation in progress..."):
            try:
                from src.quality import run_quality_pipeline
                from src.quality.impute import ImputationMethod

                # Determine imputation method
                imputation_method_str = st.session_state.get("imputation_method", "Median")
                imputation_method = (
                    ImputationMethod.MEAN if imputation_method_str == "Average"
                    else ImputationMethod.MEDIAN
                )

                # Run validation pipeline (outlier detection moved to Capacity Analysis)
                result = run_quality_pipeline(
                    st.session_state.masterdata_df,
                    enable_imputation=st.session_state.get("imputation_enabled", True),
                    imputation_method=imputation_method,
                )
                st.session_state.quality_result = result
                st.session_state.masterdata_df = result.df

                if manual_run:
                    st.toast("Validation complete", icon="✅")
                st.rerun()

            except Exception as e:
                st.error(f"Validation error: {e}")

    # Display results
    if st.session_state.quality_result is not None:
        _render_capacity_validation_results()


def _render_capacity_validation_results() -> None:
    """Display capacity validation results."""
    result = st.session_state.quality_result

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Quality Score",
            f"{result.quality_score:.1f}%",
            help=(
                "Weighted average of data coverage: dimensions (40%), weight (30%), "
                "stock (30%), minus penalty for detected issues (0.5 point per issue, max 30). "
                "Higher score indicates better data quality."
            ),
        )
    with col2:
        st.metric(
            "Records",
            result.total_records,
            help="Total number of SKU records in the masterdata file",
        )
    with col3:
        st.metric(
            "Valid",
            result.valid_records,
            help="Records with complete dimensions and weight data",
        )
    with col4:
        st.metric(
            "Imputed",
            result.imputed_records,
            help="Records with missing values filled using imputation",
        )

    render_divider()

    # Key Findings
    insights = generate_validation_insights(result)
    render_insights(insights, title="Key Findings")
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

    st.caption("Outliers (SKUs not fitting any carrier) shown in Capacity Analysis results")

    # Forward guidance to Analysis
    if st.session_state.get("capacity_result") is None:
        render_forward_guidance("Validation complete — proceed to the Analysis tab to run capacity analysis")

    # Validation help section
    with st.expander("❓ Validation help", expanded=False):
        st.markdown("""
**Missing Critical** - Required fields (SKU, dimensions, weight) with missing or zero values.
These SKUs cannot be analyzed until the data is corrected.

**Duplicates** - Same SKU appearing multiple times in the masterdata.
Each SKU should appear only once with consistent dimension data.

**Conflicts** - Same SKU with different dimension or weight values across records.
Indicates inconsistent data that needs to be resolved.

---

**Note:** Outlier and Borderline detection has been moved to **Capacity Analysis**.
This ensures outliers are detected using the configured carriers with rotation-aware fitting.
        """)
