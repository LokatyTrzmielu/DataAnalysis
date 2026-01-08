"""Performance view - performance analysis tab with shift configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st


def render_performance_view() -> None:
    """Render the Performance Analysis tab content."""
    st.header("Performance analysis")

    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    # Shift configuration
    st.markdown("**Shift configuration:**")
    shift_config = st.selectbox(
        "Shift schedule",
        options=["Default (2 shifts, Mon-Fri)", "Custom schedule", "From YAML file", "None"],
        index=0,
        help="Select shift schedule for performance analysis",
    )

    shift_schedule = None

    # Custom schedule option
    if shift_config == "Custom schedule":
        st.markdown("**Enter schedule parameters:**")
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

    if st.button("Run performance analysis"):
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

    st.markdown("---")
    st.markdown("**Analysis results:**")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Lines/h (avg)", f"{kpi.avg_lines_per_hour:.1f}")
        st.metric("Orders/h (avg)", f"{kpi.avg_orders_per_hour:.1f}")
    with col_b:
        st.metric("Peak lines/h", kpi.peak_lines_per_hour)
        st.metric("P95 lines/h", f"{kpi.p95_lines_per_hour:.1f}")

    # Additional metrics in expander
    with st.expander("Detailed statistics", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total lines", f"{kpi.total_lines:,}")
            st.metric("Total orders", f"{kpi.total_orders:,}")
        with col2:
            st.metric("Total units", f"{kpi.total_units:,}")
            if kpi.total_orders > 0:
                avg_lines_per_order = kpi.total_lines / kpi.total_orders
                st.metric("Avg lines/order", f"{avg_lines_per_order:.2f}")
