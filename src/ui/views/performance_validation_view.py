"""Performance validation view - orders data quality validation tab."""

from __future__ import annotations

import streamlit as st

from src.ui.layout import render_divider, render_section_header


def render_performance_validation_view() -> None:
    """Render the Performance Validation tab content."""
    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    df = st.session_state.orders_df

    # Basic Orders statistics
    render_section_header("Orders data summary", "📋")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total records", len(df))
    with col2:
        if "date" in df.columns:
            date_min = df["date"].min()
            date_max = df["date"].max()
            st.metric("Date range", f"{date_min} - {date_max}")
        else:
            st.metric("Date range", "N/A")
    with col3:
        has_hourly = "hour" in df.columns or "time" in df.columns
        st.metric("Hourly data", "Yes" if has_hourly else "No")

    render_divider()

    st.info(
        "Orders validation is under development. "
        "Future updates will include checks for missing SKUs, "
        "date gaps, quantity anomalies, and more."
    )
