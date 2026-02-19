"""Performance view - performance analysis tab with shift configuration."""

from __future__ import annotations

import tempfile

import streamlit as st

from src.ui.layout import render_bold_label
from src.ui.views.performance_results import render_performance_results


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
        render_performance_results()
