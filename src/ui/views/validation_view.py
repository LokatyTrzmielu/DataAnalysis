"""Validation view - data quality validation tab."""

from __future__ import annotations

import streamlit as st

from src.ui.layout import render_bold_label, render_divider, render_section_header


def render_validation_view(show_header: bool = True) -> None:
    """Render the Validation tab content.

    Args:
        show_header: Whether to display the header. Set to False when embedded in another view.
    """
    if show_header:
        st.header("✅ Validation")

    if st.session_state.masterdata_df is None:
        st.info("First import Masterdata in the Import tab")
        return

    if st.button("Run validation", key="run_validation", type="primary"):
        with st.spinner("Validation in progress..."):
            try:
                from src.quality import run_quality_pipeline
                from src.quality.impute import ImputationMethod
                from src.core.carriers import load_carriers

                # Build outlier thresholds from session state
                outlier_thresholds = {
                    "length_mm": {
                        "min": st.session_state.get("outlier_length_min", 1),
                        "max": st.session_state.get("outlier_length_max", 3000),
                    },
                    "width_mm": {
                        "min": st.session_state.get("outlier_width_min", 1),
                        "max": st.session_state.get("outlier_width_max", 3000),
                    },
                    "height_mm": {
                        "min": st.session_state.get("outlier_height_min", 1),
                        "max": st.session_state.get("outlier_height_max", 2000),
                    },
                    "weight_kg": {
                        "min": st.session_state.get("outlier_weight_min", 0.001),
                        "max": st.session_state.get("outlier_weight_max", 500.0),
                    },
                }

                # Determine imputation method
                imputation_method_str = st.session_state.get("imputation_method", "Median")
                imputation_method = (
                    ImputationMethod.MEAN if imputation_method_str == "Average"
                    else ImputationMethod.MEDIAN
                )

                # Load active carriers for rotation-aware dimensional outlier detection
                all_carriers = load_carriers()
                active_carriers = [c for c in all_carriers if c.is_active]

                result = run_quality_pipeline(
                    st.session_state.masterdata_df,
                    enable_imputation=st.session_state.get("imputation_enabled", True),
                    imputation_method=imputation_method,
                    enable_outlier_validation=st.session_state.get("outlier_validation_enabled", True),
                    outlier_thresholds=outlier_thresholds,
                    carriers=active_carriers,
                )
                st.session_state.quality_result = result
                st.session_state.masterdata_df = result.df

                st.success("Validation complete")

            except Exception as e:
                st.error(f"Validation error: {e}")

    # Display results
    if st.session_state.quality_result is not None:
        _render_validation_results()


def _render_validation_results() -> None:
    """Display validation results."""
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

    # Coverage
    render_section_header("Data coverage", "📊")
    col1, col2 = st.columns(2)

    with col1:
        render_bold_label("Before imputation:", "⬅️")
        st.progress(result.metrics_before.dimensions_coverage_pct / 100,
                   text=f"Dimensions: {result.metrics_before.dimensions_coverage_pct:.1f}%")
        st.progress(result.metrics_before.weight_coverage_pct / 100,
                   text=f"Weight: {result.metrics_before.weight_coverage_pct:.1f}%")

    with col2:
        render_bold_label("After imputation:", "➡️")
        st.progress(result.metrics_after.dimensions_coverage_pct / 100,
                   text=f"Dimensions: {result.metrics_after.dimensions_coverage_pct:.1f}%")
        st.progress(result.metrics_after.weight_coverage_pct / 100,
                   text=f"Weight: {result.metrics_after.weight_coverage_pct:.1f}%")

    # Issues
    render_section_header("Detected issues", "⚠️")
    dq = result.dq_lists
    # Show 0 for Outliers/Borderline when validation is disabled
    outliers_count = (
        len(dq.suspect_outliers)
        if st.session_state.get("outlier_validation_enabled", True)
        else 0
    )
    borderline_count = (
        len(dq.high_risk_borderline)
        if st.session_state.get("borderline_threshold", 0) > 0
        else 0
    )
    problems = {
        "Missing Critical": len(dq.missing_critical),
        "Outliers": outliers_count,
        "Borderline": borderline_count,
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

**Outliers** - Values outside the acceptable range defined in settings.
Very small or very large dimensions/weights that may indicate data entry errors.
These SKUs are **excluded from capacity analysis** and listed for verification only.

**Borderline** - SKUs with dimensions very close to carrier size limits.
These items may have fitting issues during automated storage operations.
These SKUs are **excluded from capacity analysis** and listed for verification only.

**Duplicates** - Same SKU appearing multiple times in the masterdata.
Each SKU should appear only once with consistent dimension data.

**Conflicts** - Same SKU with different dimension or weight values across records.
Indicates inconsistent data that needs to be resolved.
        """)
