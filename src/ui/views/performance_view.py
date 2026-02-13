"""Performance view - performance analysis tab with shift configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import streamlit as st

from src.ui.layout import (
    apply_plotly_dark_theme,
    render_bold_label,
    render_chart_download_button,
    render_divider,
    render_kpi_section,
    render_plotly_chart,
    render_section_header,
)
from src.ui.theme import COLORS


def render_performance_view() -> None:
    """Render the Performance Analysis tab content."""
    st.header("📈 Performance Analysis")

    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    # Performance settings
    productive_hours = st.slider(
        "Productive hours / shift",
        min_value=4.0,
        max_value=8.0,
        value=st.session_state.get("productive_hours", 7.0),
        step=0.5,
        help="Effective work time per shift",
    )
    st.session_state.productive_hours = productive_hours

    # Shift configuration
    render_bold_label("Shift configuration:", "⏰")
    shift_config = st.selectbox(
        "Shift schedule",
        options=["Default (2 shifts, Mon-Fri)", "Custom schedule", "From YAML file", "None"],
        index=0,
        help="Select shift schedule for performance analysis",
    )

    shift_schedule = None

    # Initialize custom schedule variables with defaults
    custom_days = 5
    custom_hours = 8
    custom_shifts = 2

    # Custom schedule option
    if shift_config == "Custom schedule":
        render_bold_label("Enter schedule parameters:", "📝")
        col_days, col_hours, col_shifts = st.columns(3)
        with col_days:
            custom_days = st.number_input(
                "Days per week",
                min_value=1,
                max_value=7,
                value=5,
                step=1,
                help="How many days per week the warehouse operates",
            )
        with col_hours:
            custom_hours = st.number_input(
                "Hours per day",
                min_value=1,
                max_value=24,
                value=8,
                step=1,
                help="How many hours per day of work",
            )
        with col_shifts:
            custom_shifts = st.number_input(
                "Shifts per day",
                min_value=1,
                max_value=4,
                value=2,
                step=1,
                help="How many shifts per day",
            )

        # Calculate hours per shift
        hours_per_shift = custom_hours / custom_shifts
        st.info(f"Hours per shift: {hours_per_shift:.1f}h | Total shifts/week: {custom_days * custom_shifts}")

    if shift_config == "From YAML file":
        shifts_file = st.file_uploader(
            "Schedule file (YAML)",
            type=["yml", "yaml"],
            key="shifts_upload",
        )
        if shifts_file is not None:
            from src.analytics import load_shifts

            with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmp:
                tmp.write(shifts_file.read())
                tmp_path = tmp.name

            try:
                shift_schedule = load_shifts(tmp_path)
                st.success("Schedule loaded")
            except Exception as e:
                st.error(f"Schedule loading error: {e}")

    if st.button("Run performance analysis", type="primary"):
        with st.spinner("Analysis in progress..."):
            try:
                from src.analytics import PerformanceAnalyzer
                from src.analytics.shifts import ShiftSchedule
                from src.core.types import ShiftConfig, WeeklySchedule

                # Get productive hours from session state
                productive_hours = st.session_state.get("productive_hours", 7.0)

                # Create shift schedule
                if shift_config == "Custom schedule":
                    # Generate shifts based on entered parameters
                    hours_per_shift = custom_hours / custom_shifts
                    productive_hours = min(hours_per_shift - 1, productive_hours)

                    # Generate shift configurations
                    shift_configs = []
                    start_hour = 6  # Start at 6:00
                    for s in range(custom_shifts):
                        end_hour = start_hour + int(hours_per_shift)
                        shift_configs.append(
                            ShiftConfig(
                                name=f"S{s+1}",
                                start=f"{start_hour:02d}:00",
                                end=f"{end_hour:02d}:00",
                            )
                        )
                        start_hour = end_hour

                    # Assign shifts to days of the week based on custom_days
                    days_shifts: list[list[ShiftConfig]] = [
                        shift_configs if i < custom_days else []
                        for i in range(7)
                    ]

                    weekly = WeeklySchedule(
                        productive_hours_per_shift=productive_hours,
                        mon=days_shifts[0],
                        tue=days_shifts[1],
                        wed=days_shifts[2],
                        thu=days_shifts[3],
                        fri=days_shifts[4],
                        sat=days_shifts[5],
                        sun=days_shifts[6],
                    )
                    shift_schedule = ShiftSchedule(weekly_schedule=weekly)

                elif shift_config == "Default (2 shifts, Mon-Fri)":
                    weekly = WeeklySchedule(
                        productive_hours_per_shift=productive_hours,
                        mon=[
                            ShiftConfig(name="S1", start="07:00", end="15:00"),
                            ShiftConfig(name="S2", start="15:00", end="23:00"),
                        ],
                        tue=[
                            ShiftConfig(name="S1", start="07:00", end="15:00"),
                            ShiftConfig(name="S2", start="15:00", end="23:00"),
                        ],
                        wed=[
                            ShiftConfig(name="S1", start="07:00", end="15:00"),
                            ShiftConfig(name="S2", start="15:00", end="23:00"),
                        ],
                        thu=[
                            ShiftConfig(name="S1", start="07:00", end="15:00"),
                            ShiftConfig(name="S2", start="15:00", end="23:00"),
                        ],
                        fri=[
                            ShiftConfig(name="S1", start="07:00", end="15:00"),
                            ShiftConfig(name="S2", start="15:00", end="23:00"),
                        ],
                        sat=[],
                        sun=[],
                    )
                    shift_schedule = ShiftSchedule(weekly_schedule=weekly)

                analyzer = PerformanceAnalyzer(
                    shift_schedule=shift_schedule,
                    productive_hours_per_shift=productive_hours,
                )
                result = analyzer.analyze(st.session_state.orders_df)
                st.session_state.performance_result = result
                st.session_state.analysis_complete = True

                st.toast("Performance analysis complete", icon="✅")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    # Display performance analysis results
    if st.session_state.performance_result is not None:
        _render_performance_results()


def _render_performance_results() -> None:
    """Display performance analysis results.

    Layout: KPI -> Throughput -> Daily Activity -> Heatmap -> Trends -> SKU Pareto -> Order Structure -> Detailed Stats
    """
    result = st.session_state.performance_result

    excluded = getattr(result, "excluded_nonworking_rows", 0)
    if excluded > 0:
        st.info(f"{excluded} rows from non-working days excluded from analysis (based on shift configuration)")

    render_divider()

    # 1. KPI section
    _render_performance_kpi()

    render_divider()

    # 2. Throughput chart (only when hourly data available)
    _render_throughput_chart()

    render_divider()

    # 3. Daily Activity
    render_section_header("Daily Activity", "📅")
    _render_daily_lines_chart()

    render_divider()

    # 4. Heatmap
    _render_hourly_heatmap()

    render_divider()

    # 5. Trends
    _render_trends_section()

    render_divider()

    # 6. SKU Pareto
    _render_sku_pareto_section()

    render_divider()

    # 7. Order Structure
    _render_order_structure_chart()

    render_divider()

    # 8. Detailed Statistics
    _render_detailed_stats()


def _render_performance_kpi() -> None:
    """Render KPI section with conditional hourly KPIs."""
    result = st.session_state.performance_result
    kpi = result.kpi

    render_section_header("Key Performance Indicators", "📊")

    # Always-visible KPIs
    metrics = [
        {
            "title": "Total Orders",
            "value": f"{kpi.total_orders:,}",
            "help_text": "Total number of unique orders",
        },
        {
            "title": "Total Lines",
            "value": f"{kpi.total_lines:,}",
            "help_text": "Total order lines",
        },
        {
            "title": "Avg Lines/Order",
            "value": f"{kpi.avg_lines_per_order:.2f}",
            "help_text": "Average lines per order",
        },
    ]

    # Hourly KPIs only when hourly data exists
    if result.has_hourly_data:
        # Find peak hour
        peak_hour = 0
        hourly = result.hourly_metrics
        if hourly:
            max_lines = max(h.lines for h in hourly)
            for h in hourly:
                if h.lines == max_lines:
                    peak_hour = h.hour
                    break

        metrics.extend([
            {
                "title": "Avg Lines/h",
                "value": f"{kpi.avg_lines_per_hour:.1f}",
                "help_text": "Average lines per hour (from date+hour data)",
            },
            {
                "title": "P95 Lines/h",
                "value": f"{kpi.p95_lines_per_hour:.0f}",
                "help_text": "95th percentile hourly throughput",
            },
        ])

    render_kpi_section(metrics)


def _render_throughput_chart() -> None:
    """Render throughput scatter/line chart (date+hour granularity)."""
    result = st.session_state.performance_result

    if not result.has_hourly_data:
        render_section_header("Hourly Throughput", "📈")
        st.warning("Hourly throughput analysis unavailable - import data with time information.")
        return

    datehour = result.datehour_metrics
    if not datehour:
        return

    render_section_header("Hourly Throughput", "📈")

    # Build x-axis as datetime for proper time series
    from datetime import datetime as dt
    x_vals = [dt.combine(dh.date, dt.min.time()).replace(hour=dh.hour) for dh in datehour]
    y_vals = [dh.lines for dh in datehour]

    kpi = result.kpi

    fig = go.Figure()

    # Scatter data points
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        name="Lines/h",
        marker={"color": COLORS["primary"], "size": 5, "opacity": 0.7},
        hovertemplate="%{x}<br>Lines: %{y}<extra></extra>",
    ))

    # Reference lines
    fig.add_hline(
        y=kpi.avg_lines_per_hour,
        line_dash="dash",
        line_color=COLORS["info"],
        annotation_text=f"Avg: {kpi.avg_lines_per_hour:.0f}",
        annotation_position="top left",
    )
    fig.add_hline(
        y=kpi.p90_lines_per_hour,
        line_dash="dot",
        line_color=COLORS["warning"],
        annotation_text=f"P90: {kpi.p90_lines_per_hour:.0f}",
        annotation_position="top left",
    )
    fig.add_hline(
        y=kpi.p95_lines_per_hour,
        line_dash="dot",
        line_color=COLORS["error"],
        annotation_text=f"P95: {kpi.p95_lines_per_hour:.0f}",
        annotation_position="top left",
    )

    fig.update_layout(
        title="Throughput Over Time (Lines per Hour)",
        xaxis_title="Date",
        yaxis_title="Lines / hour",
        showlegend=False,
        hovermode="closest",
    )

    apply_plotly_dark_theme(fig)
    render_plotly_chart(fig, "throughput_hourly", use_container_width=True)
    render_chart_download_button(fig, "throughput_hourly")


def _render_daily_lines_chart() -> None:
    """Render daily lines/orders line chart."""
    result = st.session_state.performance_result
    daily = result.daily_metrics

    if not daily:
        st.info("No daily metrics available.")
        return

    dates = [d.date for d in daily]
    lines = [d.lines for d in daily]
    orders = [d.orders for d in daily]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=lines,
        mode="lines+markers",
        name="Lines",
        line={"color": COLORS["primary"], "width": 2},
        marker={"size": 6},
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=orders,
        mode="lines+markers",
        name="Orders",
        line={"color": COLORS["info"], "width": 2},
        marker={"size": 6},
        yaxis="y2",
    ))

    fig.update_layout(
        title="Daily Activity",
        xaxis_title="Date",
        yaxis={"title": "Lines", "side": "left"},
        yaxis2={
            "title": "Orders",
            "side": "right",
            "overlaying": "y",
            "showgrid": False,
        },
        showlegend=True,
        legend={"x": 0, "y": 1.1, "orientation": "h"},
        hovermode="x unified",
    )

    apply_plotly_dark_theme(fig)
    render_plotly_chart(fig, "daily_activity", use_container_width=True)
    render_chart_download_button(fig, "daily_activity")


def _render_hourly_heatmap() -> None:
    """Render hourly activity heatmap by day of week."""
    result = st.session_state.performance_result

    if not result.has_hourly_data:
        return

    filtered = getattr(result, "filtered_df", None)
    orders_df = filtered if filtered is not None else st.session_state.orders_df
    if orders_df is None or "timestamp" not in orders_df.columns:
        return

    render_section_header("Hourly Activity Heatmap", "🗺️")

    heatmap_df = orders_df.filter(
        pl.col("timestamp").is_not_null()
    ).with_columns([
        pl.col("timestamp").dt.weekday().alias("day_of_week"),
        pl.col("timestamp").dt.hour().alias("hour"),
    ]).group_by(["day_of_week", "hour"]).agg(
        pl.len().alias("lines")
    ).sort(["day_of_week", "hour"])

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(24))
    matrix = [[0 for _ in range(24)] for _ in range(7)]

    for row in heatmap_df.to_dicts():
        day_idx = row["day_of_week"] - 1
        if 0 <= day_idx < 7:
            matrix[day_idx][row["hour"]] = row["lines"]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"{h:02d}:00" for h in hours],
        y=days,
        colorscale=[
            [0, COLORS["surface"]],
            [0.5, COLORS["warning"]],
            [1, COLORS["primary"]],
        ],
        hovertemplate="Day: %{y}<br>Hour: %{x}<br>Lines: %{z}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="Day of Week",
        yaxis={"autorange": "reversed"},
    )

    apply_plotly_dark_theme(fig)
    render_plotly_chart(fig, "hourly_heatmap", use_container_width=True)
    render_chart_download_button(fig, "hourly_heatmap")


def _render_trends_section() -> None:
    """Render weekly trends and day-of-week profile."""
    result = st.session_state.performance_result

    render_section_header("Trends", "📊")

    col1, col2 = st.columns(2)

    # Weekly trend bar chart
    with col1:
        weekly = result.weekly_trends
        if weekly:
            labels = [f"W{w.week_number}" for w in weekly]
            lines = [w.lines for w in weekly]

            fig = go.Figure(data=go.Bar(
                x=labels,
                y=lines,
                marker_color=COLORS["primary"],
                hovertemplate="Week %{x}<br>Lines: %{y:,}<extra></extra>",
            ))
            fig.update_layout(
                title="Weekly Trend (Lines)",
                xaxis_title="Week",
                yaxis_title="Lines",
            )
            apply_plotly_dark_theme(fig)
            render_plotly_chart(fig, "weekly_trend", use_container_width=True)
            render_chart_download_button(fig, "weekly_trend")
        else:
            st.info("Not enough data for weekly trends.")

    # Day-of-week profile
    with col2:
        weekday_profile = result.weekday_profile
        if weekday_profile:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_labels = []
            day_values = []
            for i in range(1, 8):  # Polars weekday 1=Mon, 7=Sun
                day_labels.append(day_names[i - 1])
                day_values.append(weekday_profile.get(i, 0))

            fig = go.Figure(data=go.Bar(
                x=day_labels,
                y=day_values,
                marker_color=COLORS["warning"],
                hovertemplate="%{x}<br>Avg Lines/day: %{y:.0f}<extra></extra>",
            ))
            fig.update_layout(
                title="Day-of-Week Profile (Avg Lines/Day)",
                xaxis_title="Day",
                yaxis_title="Avg Lines",
            )
            apply_plotly_dark_theme(fig)
            render_plotly_chart(fig, "day_of_week", use_container_width=True)
            render_chart_download_button(fig, "day_of_week")
        else:
            st.info("Not enough data for weekday profile.")


def _render_sku_pareto_section() -> None:
    """Render SKU Pareto chart and ABC summary."""
    result = st.session_state.performance_result
    sku_pareto = result.sku_pareto

    if not sku_pareto:
        return

    render_section_header("SKU Pareto / ABC Analysis", "📦")

    # ABC summary
    abc_counts = {"A": 0, "B": 0, "C": 0}
    abc_lines = {"A": 0, "B": 0, "C": 0}
    for s in sku_pareto:
        abc_counts[s.abc_class] += 1
        abc_lines[s.abc_class] += s.total_lines

    total_sku = len(sku_pareto)
    total_lines = sum(s.total_lines for s in sku_pareto)

    col1, col2, col3 = st.columns(3)
    with col1:
        pct_sku = abc_counts["A"] / total_sku * 100 if total_sku > 0 else 0
        pct_lines = abc_lines["A"] / total_lines * 100 if total_lines > 0 else 0
        st.metric("Class A", f"{abc_counts['A']} SKU ({pct_sku:.0f}%)",
                   delta=f"{pct_lines:.0f}% of lines")
    with col2:
        pct_sku = abc_counts["B"] / total_sku * 100 if total_sku > 0 else 0
        pct_lines = abc_lines["B"] / total_lines * 100 if total_lines > 0 else 0
        st.metric("Class B", f"{abc_counts['B']} SKU ({pct_sku:.0f}%)",
                   delta=f"{pct_lines:.0f}% of lines")
    with col3:
        pct_sku = abc_counts["C"] / total_sku * 100 if total_sku > 0 else 0
        pct_lines = abc_lines["C"] / total_lines * 100 if total_lines > 0 else 0
        st.metric("Class C", f"{abc_counts['C']} SKU ({pct_sku:.0f}%)",
                   delta=f"{pct_lines:.0f}% of lines")

    # Pareto chart (top 20)
    top_n = min(20, len(sku_pareto))
    top_skus = sku_pareto[:top_n]

    fig = go.Figure()

    # Bar: lines per SKU
    fig.add_trace(go.Bar(
        x=[s.sku for s in top_skus],
        y=[s.total_lines for s in top_skus],
        name="Lines",
        marker_color=COLORS["primary"],
        hovertemplate="%{x}<br>Lines: %{y:,}<extra></extra>",
    ))

    # Line: cumulative %
    fig.add_trace(go.Scatter(
        x=[s.sku for s in top_skus],
        y=[s.cumulative_pct for s in top_skus],
        name="Cumulative %",
        mode="lines+markers",
        line={"color": COLORS["error"], "width": 2},
        marker={"size": 5},
        yaxis="y2",
        hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=f"SKU Pareto (Top {top_n})",
        xaxis_title="SKU",
        xaxis={"tickangle": -45},
        yaxis={"title": "Lines"},
        yaxis2={
            "title": "Cumulative %",
            "side": "right",
            "overlaying": "y",
            "showgrid": False,
            "range": [0, 105],
        },
        showlegend=True,
        legend={"x": 0, "y": 1.1, "orientation": "h"},
    )

    apply_plotly_dark_theme(fig)
    render_plotly_chart(fig, "sku_pareto", use_container_width=True)
    render_chart_download_button(fig, "sku_pareto")

    # Top 20 SKU table
    with st.expander(f"Top {top_n} SKU details"):
        table_data = {
            "Rank": [s.frequency_rank for s in top_skus],
            "SKU": [s.sku for s in top_skus],
            "Lines": [s.total_lines for s in top_skus],
            "Units": [s.total_units for s in top_skus],
            "Orders": [s.total_orders for s in top_skus],
            "Cumulative %": [f"{s.cumulative_pct:.1f}%" for s in top_skus],
            "ABC": [s.abc_class for s in top_skus],
        }
        st.dataframe(pl.DataFrame(table_data), use_container_width=True)


def _render_order_structure_chart() -> None:
    """Render order structure histogram (lines per order distribution)."""
    result = st.session_state.performance_result
    filtered = getattr(result, "filtered_df", None)
    orders_df = filtered if filtered is not None else st.session_state.orders_df

    if orders_df is None or "order_id" not in orders_df.columns:
        return

    render_section_header("Order Structure", "📋")

    lines_per_order = orders_df.group_by("order_id").agg(
        pl.len().alias("lines_count")
    )

    lines_counts = lines_per_order["lines_count"].to_list()

    fig = px.histogram(
        x=lines_counts,
        nbins=30,
        labels={"x": "Lines per Order", "y": "Order Count"},
        title="Lines per Order Distribution",
    )

    fig.update_traces(marker_color=COLORS["warning"])
    apply_plotly_dark_theme(fig)
    render_plotly_chart(fig, "order_structure", use_container_width=True)
    render_chart_download_button(fig, "order_structure")


def _render_detailed_stats() -> None:
    """Render detailed statistics section."""
    result = st.session_state.performance_result
    kpi = result.kpi

    render_section_header("Detailed Statistics", "📊")

    # Summary metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Lines", f"{kpi.total_lines:,}")
    c2.metric("Total Orders", f"{kpi.total_orders:,}")
    c3.metric("Total Pieces", f"{kpi.total_units:,}")
    c4.metric("Unique SKU", f"{kpi.unique_sku:,}")

    # Additional ratio metrics
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Avg Lines/Order", f"{kpi.avg_lines_per_order:.2f}")
        st.metric("Avg Pieces/Line", f"{kpi.avg_units_per_line:.2f}")
    with col_b:
        if result.has_hourly_data:
            st.metric("P90 Lines/h", f"{kpi.p90_lines_per_hour:.0f}")
            st.metric("P95 Lines/h", f"{kpi.p95_lines_per_hour:.0f}")
            st.metric("P99 Lines/h", f"{kpi.p99_lines_per_hour:.0f}")

    # --- Throughput tables (Per Hour / Per Shift / Per Day) ---
    if result.has_hourly_data and result.daily_metrics:
        daily = result.daily_metrics
        shifts_per_day = result.shifts_per_day

        # Per-day avg/max from daily_metrics
        avg_orders_day = sum(d.orders for d in daily) / len(daily)
        max_orders_day = max(d.orders for d in daily)
        avg_lines_day = sum(d.lines for d in daily) / len(daily)
        max_lines_day = max(d.lines for d in daily)
        avg_units_day = sum(d.units for d in daily) / len(daily)
        max_units_day = max(d.units for d in daily)

        # Per-shift = per-day / shifts_per_day
        avg_orders_shift = avg_orders_day / shifts_per_day
        max_orders_shift = max_orders_day / shifts_per_day
        avg_lines_shift = avg_lines_day / shifts_per_day
        max_lines_shift = max_lines_day / shifts_per_day
        avg_units_shift = avg_units_day / shifts_per_day
        max_units_shift = max_units_day / shifts_per_day

        def _fmt(v: float) -> str:
            return f"{v:,.1f}" if v % 1 else f"{int(v):,}"

        index = ["Per Hour", "Per Shift", "Per Day"]

        st.markdown("**Orders**")
        st.dataframe(
            pd.DataFrame(
                {
                    "Avg": [_fmt(kpi.avg_orders_per_hour), _fmt(avg_orders_shift), _fmt(avg_orders_day)],
                    "Max": [_fmt(kpi.peak_orders_per_hour), _fmt(max_orders_shift), _fmt(max_orders_day)],
                },
                index=index,
            ),
            use_container_width=True,
        )

        st.markdown("**Order Lines**")
        st.dataframe(
            pd.DataFrame(
                {
                    "Avg": [_fmt(kpi.avg_lines_per_hour), _fmt(avg_lines_shift), _fmt(avg_lines_day)],
                    "Max": [_fmt(kpi.peak_lines_per_hour), _fmt(max_lines_shift), _fmt(max_lines_day)],
                },
                index=index,
            ),
            use_container_width=True,
        )

        st.markdown("**Pieces**")
        st.dataframe(
            pd.DataFrame(
                {
                    "Avg": [_fmt(kpi.avg_units_per_hour), _fmt(avg_units_shift), _fmt(avg_units_day)],
                    "Max": [_fmt(kpi.peak_units_per_hour), _fmt(max_units_shift), _fmt(max_units_day)],
                },
                index=index,
            ),
            use_container_width=True,
        )
