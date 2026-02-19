"""Performance results display - charts, KPIs, and detailed statistics.

Extracted from performance_view.py to keep the main view focused on
configuration and the run button.
"""

from __future__ import annotations

from datetime import datetime as dt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st

from src.ui.layout import (
    apply_plotly_theme,
    render_chart_download_button,
    render_divider,
    render_kpi_section,
    render_plotly_chart,
    render_section_header,
)
from src.ui.theme import COLORS


def render_performance_results() -> None:
    """Display performance analysis results.

    Layout: Insights -> KPI -> Throughput -> Daily Activity -> Heatmap -> Trends -> SKU Pareto -> Order Structure -> Detailed Stats
    """
    from src.ui.insights import generate_performance_insights, render_insights

    result = st.session_state.performance_result

    excluded = getattr(result, "excluded_nonworking_rows", 0)
    if excluded > 0:
        st.info(f"{excluded} rows from non-working days excluded from analysis (based on shift configuration)")

    render_divider()

    # 0. Key Findings / Insight Layer
    insights = generate_performance_insights()
    render_insights(insights, title="Key Findings")

    render_divider()

    # 1. KPI section
    render_performance_kpi()

    render_divider()

    # 2. Throughput chart (only when hourly data available)
    render_throughput_chart()

    render_divider()

    # 3. Daily Activity
    render_section_header("Daily Activity", "📅")
    render_daily_lines_chart()

    render_divider()

    # 4. Heatmap
    render_hourly_heatmap()

    render_divider()

    # 5. Trends
    render_trends_section()

    render_divider()

    # 6. SKU Pareto
    render_sku_pareto_section()

    render_divider()

    # 7. Order Structure
    render_order_structure_chart()

    render_divider()

    # 8. Detailed Statistics
    render_detailed_stats()


def render_performance_kpi() -> None:
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


def render_throughput_chart() -> None:
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

    apply_plotly_theme(fig)
    render_plotly_chart(fig, "throughput_hourly", use_container_width=True)
    render_chart_download_button(fig, "throughput_hourly")


def render_daily_lines_chart() -> None:
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

    apply_plotly_theme(fig)
    render_plotly_chart(fig, "daily_activity", use_container_width=True)
    render_chart_download_button(fig, "daily_activity")


def render_hourly_heatmap() -> None:
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
            [0, "#faf9f6"],
            [0.25, "#e8d9a0"],
            [0.5, "#c9a227"],
            [0.75, "#a8861f"],
            [1, "#6b5a1e"],
        ],
        hovertemplate="Day: %{y}<br>Hour: %{x}<br>Lines: %{z}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="Day of Week",
        yaxis={"autorange": "reversed"},
    )

    apply_plotly_theme(fig)
    render_plotly_chart(fig, "hourly_heatmap", use_container_width=True)
    render_chart_download_button(fig, "hourly_heatmap")


def render_trends_section() -> None:
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
            apply_plotly_theme(fig)
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
            apply_plotly_theme(fig)
            render_plotly_chart(fig, "day_of_week", use_container_width=True)
            render_chart_download_button(fig, "day_of_week")
        else:
            st.info("Not enough data for weekday profile.")


def render_sku_pareto_section() -> None:
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

    apply_plotly_theme(fig)
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


def render_order_structure_chart() -> None:
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
    apply_plotly_theme(fig)
    render_plotly_chart(fig, "order_structure", use_container_width=True)
    render_chart_download_button(fig, "order_structure")


def render_detailed_stats() -> None:
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
