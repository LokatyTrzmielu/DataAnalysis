"""Capacity view - capacity analysis tab with carrier management."""

from __future__ import annotations

import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.core.types import CarrierConfig
from src.ui.layout import (
    apply_plotly_dark_theme,
    render_bold_label,
    render_divider,
    render_kpi_section,
    render_section_header,
    render_spacer,
    render_status_button,
)
from src.ui.theme import COLORS


def render_carrier_form() -> None:
    """Form for adding a new carrier."""
    render_bold_label("Add new carrier:", "➕")

    with st.form("add_carrier_form", clear_on_submit=True):
        render_bold_label("Internal dimensions (mm):", "📐")
        col_w, col_l, col_h = st.columns(3)
        with col_w:
            width_mm = st.number_input(
                "Width (W)",
                min_value=1,
                value=400,
                step=10,
                help="Internal width in mm",
            )
        with col_l:
            length_mm = st.number_input(
                "Length (L)",
                min_value=1,
                value=600,
                step=10,
                help="Internal length in mm",
            )
        with col_h:
            height_mm = st.number_input(
                "Height (H)",
                min_value=1,
                value=200,
                step=10,
                help="Internal height in mm",
            )

        max_weight = st.number_input(
            "Max weight (kg)",
            min_value=1,
            value=100,
            step=5,
            help="Maximum allowed load weight in kg",
        )

        # Optional ID and name fields
        with st.expander("🏷️ Optional: ID and name", expanded=False):
            col_id, col_name = st.columns(2)
            with col_id:
                carrier_id = st.text_input(
                    "Carrier ID",
                    placeholder="(auto)",
                    help="Unique identifier - leave empty for auto-generation",
                )
            with col_name:
                carrier_name = st.text_input(
                    "Name",
                    placeholder="(auto)",
                    help="Descriptive name - leave empty for auto-generation",
                )

        # Option to save permanently
        save_to_file = st.checkbox(
            "Save permanently",
            value=False,
            help="Save carrier to file - will be available in future sessions",
        )

        submitted = st.form_submit_button("Add carrier", type="primary")

        if submitted:
            from src.core.carriers import CarrierService

            # Auto-generate ID and name if empty
            existing_ids = [c["carrier_id"] for c in st.session_state.custom_carriers]

            if not carrier_id:
                # Generate unique ID based on dimensions
                base_id = f"CARRIER_{width_mm}x{length_mm}x{height_mm}"
                carrier_id = base_id
                counter = 1
                while carrier_id in existing_ids:
                    carrier_id = f"{base_id}_{counter}"
                    counter += 1

            if not carrier_name:
                carrier_name = f"Carrier {width_mm}x{length_mm}x{height_mm}mm"

            # Check if ID already exists (if manually provided)
            if carrier_id in existing_ids:
                st.error(f"Carrier with ID '{carrier_id}' already exists")
            else:
                new_carrier = {
                    "carrier_id": carrier_id,
                    "name": carrier_name,
                    "inner_length_mm": float(length_mm),
                    "inner_width_mm": float(width_mm),
                    "inner_height_mm": float(height_mm),
                    "max_weight_kg": float(max_weight),
                    "is_predefined": False,
                    "is_active": True,
                    "priority": None,  # No priority by default - excluded from Prioritized mode
                }
                st.session_state.custom_carriers.append(new_carrier)

                # Save to file if requested
                if save_to_file:
                    service = CarrierService()
                    custom_list = [
                        CarrierConfig(**c)
                        for c in st.session_state.custom_carriers
                        if not c.get("is_predefined", False)
                    ]
                    service.save_custom_carriers(custom_list)
                    st.success(f"Added and saved carrier: {carrier_name}")
                else:
                    st.success(f"Added carrier: {carrier_name} (this session only)")
                st.rerun()


def render_carriers_table() -> None:
    """Display table of defined carriers with delete option and activation toggle."""
    carriers = st.session_state.custom_carriers

    if not carriers:
        st.info("No carriers defined. Add carriers below.")
        return

    render_bold_label("Defined carriers:", "📦")

    # Header row
    header_cols = st.columns([1, 1, 3, 3, 2, 1, 1])
    with header_cols[0]:
        render_bold_label("Active", size="small")
    with header_cols[1]:
        render_bold_label("Priority", size="small")
    with header_cols[2]:
        render_bold_label("Carrier", size="small")
    with header_cols[3]:
        render_bold_label("Dimensions (L×W×H)", size="small")
    with header_cols[4]:
        render_bold_label("Max weight", size="small")
    with header_cols[5]:
        render_bold_label("Type", size="small")
    with header_cols[6]:
        st.markdown("")

    for i, carrier in enumerate(carriers):
        is_predefined = carrier.get("is_predefined", False)
        is_active = carrier.get("is_active", True)
        current_priority = carrier.get("priority")
        cols = st.columns([1, 1, 3, 3, 2, 1, 1])

        with cols[0]:
            # Checkbox for activation/deactivation
            new_active = st.checkbox(
                "Active",
                value=is_active,
                key=f"carrier_active_{i}",
                label_visibility="collapsed",
                help="Include this carrier in analysis",
            )
            if new_active != is_active:
                st.session_state.custom_carriers[i]["is_active"] = new_active
                st.rerun()

        with cols[1]:
            # Priority input (0 or empty = no priority = excluded from Prioritized mode)
            new_priority = st.number_input(
                "Priority",
                min_value=0,
                max_value=99,
                value=current_priority if current_priority is not None else 0,
                key=f"carrier_priority_{i}",
                label_visibility="collapsed",
                help="Priority for Prioritized mode (1=first, 0=excluded)",
            )
            # Convert 0 to None (no priority)
            new_priority_value = new_priority if new_priority > 0 else None
            if new_priority_value != current_priority:
                st.session_state.custom_carriers[i]["priority"] = new_priority_value
                st.rerun()

        with cols[2]:
            st.text(f"{carrier['carrier_id']}")
            st.caption(carrier["name"])
        with cols[3]:
            dims = f"{int(carrier['inner_length_mm'])}×{int(carrier['inner_width_mm'])}×{int(carrier['inner_height_mm'])} mm"
            st.text(dims)
        with cols[4]:
            st.text(f"{carrier['max_weight_kg']:.1f} kg")
        with cols[5]:
            if is_predefined:
                render_status_button("Predef.", "in_progress", show_icon=False)
            else:
                render_status_button("Custom", "success", show_icon=False)
        with cols[6]:
            if is_predefined:
                # Cannot delete predefined carriers
                st.button(
                    "🔒", key=f"lock_carrier_{i}", disabled=True, help="Predefined"
                )
            else:
                # Can delete custom carriers
                if st.button(
                    "✕", key=f"del_carrier_{i}", help=f"Delete {carrier['name']}"
                ):
                    st.session_state.custom_carriers.pop(i)
                    st.rerun()


def render_capacity_view() -> None:
    """Render the Capacity Analysis tab content."""
    st.header("📊 Capacity Analysis")

    if st.session_state.masterdata_df is None:
        st.info("Import Masterdata in the Import tab first")
        return

    # Display carriers table
    render_carriers_table()

    # Save all custom carriers button
    custom_count = sum(
        1
        for c in st.session_state.custom_carriers
        if not c.get("is_predefined", False)
    )
    if custom_count > 0:
        if st.button(
            f"Save {custom_count} custom carrier(s) permanently",
            help="Save all custom carriers to config file",
        ):
            from src.core.carriers import CarrierService

            service = CarrierService()
            custom_list = [
                CarrierConfig(**c)
                for c in st.session_state.custom_carriers
                if not c.get("is_predefined", False)
            ]
            service.save_custom_carriers(custom_list)
            st.success(f"Saved {len(custom_list)} carrier(s)")

    render_divider()

    # Carrier addition form
    with st.expander("➕ Add carrier", expanded=len(st.session_state.custom_carriers) == 0):
        render_carrier_form()

    # Analysis button
    carriers_defined = len(st.session_state.custom_carriers) > 0

    if not carriers_defined:
        st.warning("Add at least one carrier for analysis")

    # Analysis mode selection
    render_divider()
    analysis_mode = st.radio(
        "Analysis mode",
        options=["Independent (all carriers)", "Prioritized (by priority)"],
        index=0,
        key="capacity_analysis_mode",
        help="Independent: SKU tested vs all active carriers separately. "
             "Prioritized: SKU assigned to first fitting carrier by priority (1=first). "
             "Carriers with priority=0 are excluded from Prioritized mode.",
        horizontal=True,
    )
    prioritization_mode = analysis_mode == "Prioritized (by priority)"

    if prioritization_mode:
        # Count carriers with priority set
        carriers_with_priority = [
            c for c in st.session_state.custom_carriers
            if c.get("is_active", True) and c.get("priority") is not None and c.get("priority", 0) > 0
        ]
        priority_count = len(carriers_with_priority)

        if priority_count == 0:
            st.warning(
                "No carriers have priority set. Set priority > 0 for carriers to include them "
                "in Prioritized analysis. Carriers with priority=0 are excluded."
            )
        else:
            st.info(
                f"Prioritized mode: {priority_count} carrier(s) with priority will be used. "
                "Each SKU assigned to first fitting carrier by priority (1=first, 2=second, ...). "
                "Set priority in the table above."
            )

    # Exclusion settings
    outlier_count = 0
    if st.session_state.quality_result is not None:
        outlier_count = len({item.sku for item in st.session_state.quality_result.dq_lists.suspect_outliers})

    with st.expander(
        f"⚠️ Exclusion settings ({outlier_count} outliers)" if outlier_count > 0 else "⚠️ Exclusion settings",
        expanded=outlier_count > 0,
    ):
        if outlier_count > 0:
            st.warning(f"{outlier_count} SKU detected as outliers (values outside normal range)")

        st.checkbox(
            f"Exclude outliers ({outlier_count} SKU)",
            value=outlier_count > 0,  # Default: enabled only when outliers exist
            key="exclude_outliers_checkbox",
            disabled=outlier_count == 0,
            help="SKU with suspicious values (dimensions/weight outside normal range)",
        )

        if outlier_count == 0:
            st.caption("No outliers detected - all SKU will be included in analysis")
        else:
            st.caption("Borderline filters will be available after running analysis")

    if st.button("Run capacity analysis", disabled=not carriers_defined, type="primary"):
        with st.spinner("Analysis in progress..."):
            try:
                from src.analytics import CapacityAnalyzer

                # Convert dictionaries to CarrierConfig
                carriers = [
                    CarrierConfig(**c)
                    for c in st.session_state.custom_carriers
                ]

                # Use borderline threshold from session state
                borderline_threshold = st.session_state.get("borderline_threshold", 2.0)

                # Filter out only Outliers from analysis (borderline handled per carrier in UI)
                df_to_analyze = st.session_state.masterdata_df
                excluded_outliers_count = 0

                if st.session_state.quality_result is not None:
                    dq = st.session_state.quality_result.dq_lists

                    # Exclude outliers if checkbox is checked
                    if st.session_state.get("exclude_outliers_checkbox", True):
                        outlier_skus = {item.sku for item in dq.suspect_outliers}
                        if outlier_skus:
                            excluded_outliers_count = len(outlier_skus)
                            df_to_analyze = df_to_analyze.filter(
                                ~pl.col("sku").is_in(list(outlier_skus))
                            )

                analyzer = CapacityAnalyzer(
                    carriers=carriers,
                    borderline_threshold_mm=borderline_threshold,
                )
                result = analyzer.analyze_dataframe(
                    df_to_analyze,
                    prioritization_mode=prioritization_mode,
                )
                st.session_state.capacity_result = result
                st.session_state.capacity_excluded_outliers = excluded_outliers_count
                st.session_state.capacity_prioritization_mode = prioritization_mode
                st.session_state.capacity_threshold_used = borderline_threshold

                st.toast("Capacity analysis complete", icon="✅")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    # Display capacity analysis results
    if st.session_state.capacity_result is not None:
        _render_capacity_results()


def _render_capacity_kpi() -> None:
    """Render KPI section with 4 cards: SKU count, fit %, avg dimensions, avg weight."""
    df = st.session_state.masterdata_df
    result = st.session_state.capacity_result

    if df is None:
        return

    # Calculate KPIs from masterdata
    total_sku = len(df)

    # Average fit percentage across all carriers (excluding NONE)
    fit_percentages = []
    for carrier_id, stats in result.carrier_stats.items():
        total_count = stats.fit_count + stats.borderline_count + stats.not_fit_count
        if carrier_id != "NONE" and total_count > 0:
            fit_percentages.append(stats.fit_percentage)
    avg_fit_pct = sum(fit_percentages) / len(fit_percentages) if fit_percentages else 0

    # Average dimensions (L×W×H)
    avg_length = df.select(pl.col("length_mm").mean()).item() or 0
    avg_width = df.select(pl.col("width_mm").mean()).item() or 0
    avg_height = df.select(pl.col("height_mm").mean()).item() or 0

    # Average weight
    avg_weight = df.select(pl.col("weight_kg").mean()).item() or 0

    render_section_header("Key Performance Indicators", "📊")

    metrics = [
        {
            "title": "SKU Count",
            "value": f"{total_sku:,}",
            "help_text": "Total number of SKU in analysis",
        },
        {
            "title": "Avg Fit %",
            "value": f"{avg_fit_pct:.1f}%",
            "help_text": "Average fit percentage across all carriers",
        },
        {
            "title": "Avg Dimensions",
            "value": f"{avg_length:.0f}×{avg_width:.0f}×{avg_height:.0f}",
            "help_text": "Average L×W×H in mm",
        },
        {
            "title": "Avg Weight",
            "value": f"{avg_weight:.2f} kg",
            "help_text": "Average weight in kg",
        },
    ]

    render_kpi_section(metrics)
    render_spacer()


def _render_dimensions_histogram() -> None:
    """Render histogram of dimensions (Length, Width, Height)."""
    df = st.session_state.masterdata_df
    if df is None:
        return

    # Prepare data for histogram
    length_data = df.select(pl.col("length_mm")).to_series().to_list()
    width_data = df.select(pl.col("width_mm")).to_series().to_list()
    height_data = df.select(pl.col("height_mm")).to_series().to_list()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=length_data,
        name="Length",
        opacity=0.7,
        marker_color=COLORS["warning"],
    ))
    fig.add_trace(go.Histogram(
        x=width_data,
        name="Width",
        opacity=0.7,
        marker_color=COLORS["primary"],
    ))
    fig.add_trace(go.Histogram(
        x=height_data,
        name="Height",
        opacity=0.7,
        marker_color=COLORS["info"],
    ))

    fig.update_layout(
        title="Dimensions Distribution (mm)",
        xaxis_title="Dimension (mm)",
        yaxis_title="Count",
        barmode="overlay",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    apply_plotly_dark_theme(fig)
    st.plotly_chart(fig, width="stretch")


def _render_carrier_fit_chart() -> None:
    """Render bar chart showing FIT/BORDERLINE/NOT_FIT per carrier."""
    result = st.session_state.capacity_result
    is_prioritized = st.session_state.get("capacity_prioritization_mode", False)

    carriers = []
    fit_counts = []
    borderline_counts = []
    not_fit_counts = []

    for carrier_id, stats in result.carrier_stats.items():
        if carrier_id == "NONE":
            continue
        carriers.append(stats.carrier_name)
        fit_counts.append(stats.fit_count)
        borderline_counts.append(stats.borderline_count)
        not_fit_counts.append(stats.not_fit_count)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="FIT",
        x=carriers,
        y=fit_counts,
        marker_color=COLORS["primary"],
    ))
    fig.add_trace(go.Bar(
        name="BORDERLINE",
        x=carriers,
        y=borderline_counts,
        marker_color=COLORS["warning"],
    ))

    if not is_prioritized:
        fig.add_trace(go.Bar(
            name="NOT FIT",
            x=carriers,
            y=not_fit_counts,
            marker_color=COLORS["error"],
        ))

    title = "SKU Assignment per Carrier" if is_prioritized else "Carrier Fit Analysis"
    fig.update_layout(
        title=title,
        xaxis_title="Carrier",
        yaxis_title="SKU Count",
        barmode="stack",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    apply_plotly_dark_theme(fig)
    st.plotly_chart(fig, width="stretch")


def _render_weight_histogram() -> None:
    """Render histogram of weight distribution."""
    df = st.session_state.masterdata_df
    if df is None:
        return

    weight_data = df.select(pl.col("weight_kg")).to_series().to_list()

    fig = px.histogram(
        x=weight_data,
        nbins=30,
        title="Weight Distribution (kg)",
        labels={"x": "Weight (kg)", "y": "Count"},
        color_discrete_sequence=[COLORS["warning"]],
    )

    fig.update_layout(
        xaxis_title="Weight (kg)",
        yaxis_title="Count",
        showlegend=False,
    )

    apply_plotly_dark_theme(fig)
    st.plotly_chart(fig, width="stretch")


def _render_capacity_charts() -> None:
    """Render all capacity analysis charts."""
    render_section_header("Charts", "📈")

    col1, col2 = st.columns(2)

    with col1:
        _render_dimensions_histogram()

    with col2:
        _render_carrier_fit_chart()

    # Weight histogram in full width
    _render_weight_histogram()


def _render_capacity_table() -> None:
    """Render results table with filtering and CSV export."""
    result = st.session_state.capacity_result

    render_section_header("Results Table", "📋")

    # Get the results dataframe
    if result.df is None or result.df.height == 0:
        st.info("No results available.")
        return

    results_df = result.df

    # Filter options
    col_filter, col_carrier, col_export = st.columns([2, 2, 1])

    with col_filter:
        # Status filter
        status_options = ["All", "FIT", "BORDERLINE", "NOT_FIT"]
        selected_status = st.selectbox(
            "Filter by status",
            status_options,
            key="capacity_table_status_filter",
        )

    with col_carrier:
        # Carrier filter
        carrier_options = ["All"] + list(results_df["carrier_id"].unique().to_list())
        selected_carrier = st.selectbox(
            "Filter by carrier",
            carrier_options,
            key="capacity_table_carrier_filter",
        )

    # Apply filters
    filtered_df = results_df
    if selected_status != "All":
        filtered_df = filtered_df.filter(pl.col("fit_status") == selected_status)
    if selected_carrier != "All":
        filtered_df = filtered_df.filter(pl.col("carrier_id") == selected_carrier)

    # Rename columns for display
    display_df = filtered_df.select([
        pl.col("sku").alias("SKU"),
        pl.col("carrier_id").alias("Carrier"),
        pl.col("fit_status").alias("Status"),
        pl.col("units_per_carrier").alias("Units/Carrier"),
        pl.col("volume_m3").alias("Volume (m³)"),
        pl.col("limiting_factor").alias("Limiting Factor"),
    ])

    # Display table
    st.dataframe(
        display_df.to_pandas(),
        width="stretch",
        height=400,
    )

    # Export button
    with col_export:
        render_spacer(20)  # Align with selectbox
        render_spacer(10)  # Additional spacing
        csv_data = filtered_df.write_csv()
        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name="capacity_analysis_results.csv",
            mime="text/csv",
            width="stretch",
        )

    st.caption(f"Showing {len(filtered_df):,} of {len(results_df):,} rows")


def _render_capacity_results() -> None:
    """Display capacity analysis results."""
    result = st.session_state.capacity_result
    is_prioritized = st.session_state.get("capacity_prioritization_mode", False)

    # Check if settings changed since last analysis
    threshold_used = st.session_state.get("capacity_threshold_used", 2.0)
    current_threshold = st.session_state.get("borderline_threshold", 2.0)

    if threshold_used != current_threshold:
        st.warning(
            f"Settings changed. Results calculated with threshold {threshold_used} mm, "
            f"current setting is {current_threshold} mm. Re-run analysis to update."
        )

    render_divider()

    # === NEW: KPI Section ===
    _render_capacity_kpi()

    render_divider()

    # === NEW: Charts Section ===
    _render_capacity_charts()

    render_divider()

    # === NEW: Results Table ===
    _render_capacity_table()

    render_divider()

    # Show analysis mode info
    render_section_header("Carrier Details", "📦")
    if is_prioritized:
        st.caption("Prioritized mode - SKU assigned to smallest fitting carrier")
    else:
        st.caption("Independent mode - each SKU tested vs all carriers")

    # Show excluded outliers count if any
    excluded_outliers = st.session_state.get("capacity_excluded_outliers", 0)
    if excluded_outliers > 0:
        st.info(f"Excluded from analysis: {excluded_outliers} outlier SKU")

    # Borderline filters per carrier (only in independent mode)
    if not is_prioritized:
        with st.expander("🔧 Filter borderline SKU", expanded=False):
            st.caption("Exclude borderline from statistics per carrier:")
            for carrier_id in result.carriers_analyzed:
                stats = result.carrier_stats.get(carrier_id)
                if stats and stats.borderline_count > 0:
                    st.checkbox(
                        f"{stats.carrier_name}: {stats.borderline_count} borderline SKU",
                        value=False,
                        key=f"exclude_borderline_{carrier_id}",
                    )

    # Display results for each carrier separately
    for carrier_id in result.carriers_analyzed:
        stats = result.carrier_stats.get(carrier_id)
        if stats:
            # Special handling for "NONE" in prioritized mode
            if carrier_id == "NONE":
                with st.expander("❌ Does not fit any carrier", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "SKU count", stats.not_fit_count,
                            help="Number of SKU that don't fit any active carrier"
                        )
                    with col2:
                        st.metric(
                            "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                            help="Sum of unit volumes for non-fitting SKU"
                        )
                    with col3:
                        st.metric(
                            "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                            help="Sum of stock volumes for non-fitting SKU"
                        )
                continue

            # Check if borderline should be excluded for this carrier
            exclude_borderline = st.session_state.get(
                f"exclude_borderline_{carrier_id}", False
            )

            # Calculate display values based on filter
            if exclude_borderline and not is_prioritized:
                display_fit = stats.fit_count
                display_borderline = 0
                display_total = stats.fit_count + stats.not_fit_count
                display_fit_pct = (
                    (stats.fit_count / display_total * 100)
                    if display_total > 0
                    else 0
                )
                borderline_help = "EXCLUDED from statistics"
            else:
                display_fit = stats.fit_count
                display_borderline = stats.borderline_count
                display_fit_pct = stats.fit_percentage
                borderline_help = "SKU fitting but with margin < threshold (risk of fitting issues)"

            # In prioritized mode, show "Assigned SKU" instead of FIT/NOT_FIT
            if is_prioritized:
                assigned_count = stats.fit_count + stats.borderline_count
                with st.expander(f"📦 {stats.carrier_name} ({carrier_id})", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Assigned SKU", assigned_count,
                            help="Number of SKU assigned to this carrier (smallest fitting)"
                        )
                        if stats.borderline_count > 0:
                            st.caption(f"({stats.borderline_count} borderline)")
                    with col2:
                        st.metric(
                            "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                            help="Sum of unit volumes (L×W×H) for assigned SKU"
                        )
                    with col3:
                        st.metric(
                            "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                            help="Sum of (unit volume × stock quantity) for assigned SKU"
                        )
            else:
                with st.expander(f"📦 {stats.carrier_name} ({carrier_id})", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "FIT", display_fit,
                            help="SKU fitting completely with margin > threshold"
                        )
                        st.metric(
                            "BORDERLINE",
                            display_borderline if not exclude_borderline else f"({stats.borderline_count})",
                            help=borderline_help,
                        )
                    with col2:
                        st.metric(
                            "NOT FIT", stats.not_fit_count,
                            help="SKU not fitting in this carrier (size or weight exceeded)"
                        )
                        st.metric(
                            "Fit %", f"{display_fit_pct:.1f}%",
                            help="Percentage of SKU fitting (FIT + BORDERLINE) / Total"
                            if not exclude_borderline
                            else "Percentage of SKU fitting (FIT only) / Total (excl. borderline)"
                        )
                    with col3:
                        st.metric(
                            "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                            help="Sum of unit volumes (L×W×H) for all fitting SKU"
                        )
                        st.metric(
                            "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                            help="Sum of (unit volume × stock quantity) for all fitting SKU"
                        )
