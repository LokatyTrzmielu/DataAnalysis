"""Performance view - performance analysis tab with shift configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st

from src.ui.layout import (
    apply_plotly_dark_theme,
    render_bold_label,
    render_divider,
    render_kpi_section,
    render_section_header,
)
from src.ui.theme import COLORS


def render_performance_view() -> None:
    """Render the Performance Analysis tab content."""
    st.header("Performance analysis")

    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    # Shift configuration
    render_bold_label("Shift configuration:", "⏰")
    shift_config = st.selectbox(
        "Shift schedule",
        options=["Default (2 shifts, Mon-Fri)", "Custom schedule", "From YAML file", "None"],
        index=0,
        help="Select shift schedule for performance analysis",
    )

    shift_schedule = None

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

                    # Assign shifts to days of the week
                    days_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                    weekly_kwargs = {"productive_hours_per_shift": productive_hours}
                    for i, day in enumerate(days_map):
                        if i < custom_days:
                            weekly_kwargs[day] = shift_configs
                        else:
                            weekly_kwargs[day] = []

                    weekly = WeeklySchedule(**weekly_kwargs)
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

                st.success("Performance analysis complete")

            except Exception as e:
                st.error(f"Error: {e}")

    # Display performance analysis results
    if st.session_state.performance_result is not None:
        _render_performance_results()


def _render_performance_results() -> None:
    """Display performance analysis results."""
    result = st.session_state.performance_result
    kpi = result.kpi

    render_divider()

    # New KPI section
    _render_performance_kpi()

    render_divider()

    # New charts section
    _render_performance_charts()

    render_divider()

    # Detailed statistics section
    render_section_header("Detailed Statistics", "📊")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(
            "Lines/h (avg)",
            f"{kpi.avg_lines_per_hour:.1f}",
            help="Average order lines processed per hour",
        )
        st.metric(
            "Orders/h (avg)",
            f"{kpi.avg_orders_per_hour:.1f}",
            help="Average number of orders processed per hour",
        )
        st.metric(
            "Total lines",
            f"{kpi.total_lines:,}",
            help="Total number of order lines in the dataset",
        )
    with col_b:
        st.metric(
            "Peak lines/h",
            kpi.peak_lines_per_hour,
            help="Maximum lines per hour observed (busiest hour)",
        )
        st.metric(
            "P95 lines/h",
            f"{kpi.p95_lines_per_hour:.1f}",
            help="95th percentile of hourly line throughput",
        )
        st.metric(
            "Total units",
            f"{kpi.total_units:,}",
            help="Total number of units (quantity) across all lines",
        )


def _render_performance_kpi() -> None:
    """Render KPI section with 4 cards."""
    result = st.session_state.performance_result
    kpi = result.kpi

    # Find peak hour
    hourly = result.hourly_metrics
    peak_hour = 0
    if hourly:
        max_lines = max(h.lines for h in hourly)
        for h in hourly:
            if h.lines == max_lines:
                peak_hour = h.hour
                break

    render_section_header("Key Performance Indicators", "📊")

    metrics = [
        {
            "title": "Avg Lines/h",
            "value": f"{kpi.avg_lines_per_hour:.1f}",
            "help_text": "Average lines per hour across all hours",
        },
        {
            "title": "Peak Hour",
            "value": f"{peak_hour:02d}:00",
            "help_text": f"Hour with highest activity ({kpi.peak_lines_per_hour} lines)",
        },
        {
            "title": "Total Orders",
            "value": f"{kpi.total_orders:,}",
            "help_text": "Total number of unique orders",
        },
        {
            "title": "Avg Lines/Order",
            "value": f"{kpi.avg_lines_per_order:.2f}",
            "help_text": "Average lines per order",
        },
    ]

    render_kpi_section(metrics)


def _render_daily_lines_chart() -> None:
    """Render daily lines/orders line chart."""
    result = st.session_state.performance_result
    daily = result.daily_metrics

    if not daily:
        st.info("No daily metrics available.")
        return

    # Prepare data
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
    st.plotly_chart(fig, width="stretch")


def _render_hourly_heatmap() -> None:
    """Render hourly activity heatmap by day of week."""
    orders_df = st.session_state.orders_df

    if orders_df is None or "timestamp" not in orders_df.columns:
        st.info("No timestamp data available for heatmap.")
        return

    # Filter out null timestamps and aggregate by day of week (0=Mon) and hour
    heatmap_df = orders_df.filter(
        pl.col("timestamp").is_not_null()
    ).with_columns([
        pl.col("timestamp").dt.weekday().alias("day_of_week"),
        pl.col("timestamp").dt.hour().alias("hour"),
    ]).group_by(["day_of_week", "hour"]).agg(
        pl.len().alias("lines")
    ).sort(["day_of_week", "hour"])

    # Create matrix (7 days x 24 hours)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(24))

    # Initialize with zeros
    matrix = [[0 for _ in range(24)] for _ in range(7)]

    for row in heatmap_df.to_dicts():
        day_idx = row["day_of_week"] - 1  # Polars weekday is 1-7
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
        title="Hourly Activity Heatmap",
        xaxis_title="Hour",
        yaxis_title="Day of Week",
        yaxis={"autorange": "reversed"},
    )

    apply_plotly_dark_theme(fig)
    st.plotly_chart(fig, width="stretch")


def _render_order_structure_chart() -> None:
    """Render order structure histogram (lines per order distribution)."""
    orders_df = st.session_state.orders_df

    if orders_df is None or "order_id" not in orders_df.columns:
        st.info("No order data available.")
        return

    # Calculate lines per order
    lines_per_order = orders_df.group_by("order_id").agg(
        pl.len().alias("lines_count")
    )

    lines_counts = lines_per_order["lines_count"].to_list()

    fig = px.histogram(
        x=lines_counts,
        nbins=30,
        labels={"x": "Lines per Order", "y": "Order Count"},
        title="Order Structure (Lines per Order)",
    )

    fig.update_traces(marker_color=COLORS["warning"])
    apply_plotly_dark_theme(fig)
    st.plotly_chart(fig, width="stretch")


def _render_performance_charts() -> None:
    """Render all performance charts."""
    render_section_header("Performance Charts", "📈")

    col1, col2 = st.columns(2)

    with col1:
        _render_daily_lines_chart()

    with col2:
        _render_hourly_heatmap()

    # Full width chart
    _render_order_structure_chart()
