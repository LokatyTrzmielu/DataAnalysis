"""Performance validation view - orders data quality validation tab."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import streamlit as st

from src.ui.layout import render_bold_label, render_divider, render_section_header


def render_performance_validation_view() -> None:
    """Render the Performance Validation tab content."""
    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    df = st.session_state.orders_df

    # --- Orders data summary ---
    render_section_header("Orders data summary", "📋")

    # Row 1: 3 columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total records", len(df))
    with col2:
        if "order_date" in df.columns:
            date_min = df["order_date"].min()
            date_max = df["order_date"].max()
            st.metric("Date range", f"{date_min} - {date_max}")
        else:
            st.metric("Date range", "N/A")
    with col3:
        has_hourly = "order_hour" in df.columns and df["order_hour"].n_unique() > 1
        st.metric("Hourly data", "Yes" if has_hourly else "No")

    # Row 2: 3 columns (last one empty)
    col4, col5, _col6 = st.columns(3)
    with col4:
        if "sku" in df.columns:
            st.metric("Unique SKUs", df["sku"].n_unique())
        else:
            st.metric("Unique SKUs", "N/A")
    with col5:
        if "order_date" in df.columns:
            st.metric("Unique days", df["order_date"].n_unique())
        else:
            st.metric("Unique days", "N/A")

    render_divider()

    # --- Missing SKUs ---
    _render_missing_skus(df)
    render_divider()

    # --- Date gaps ---
    _render_date_gaps(df)
    render_divider()

    # --- Quantity anomalies ---
    _render_quantity_anomalies(df)
    render_divider()

    # --- Working pattern profile ---
    _render_working_pattern(df)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_missing_skus(df: pl.DataFrame) -> None:
    """Detect and display rows with missing or invalid SKU values."""
    render_section_header("Missing SKUs", "🔍")

    if "sku" not in df.columns:
        st.info("No `sku` column found in the data.")
        return

    invalid_values = {"", "N/A", "n/a", "-"}
    mask = (
        df["sku"].is_null()
        | df["sku"].cast(pl.Utf8).str.strip_chars().is_in(list(invalid_values))
        | (df["sku"].cast(pl.Utf8).str.strip_chars() == "")
    )
    bad_rows = df.filter(mask)
    count = len(bad_rows)

    if count == 0:
        st.success("Missing SKUs: 0")
    else:
        st.warning(f"Missing SKUs: {count} rows with null, empty, or placeholder SKU values")
        with st.expander(f"Show sample rows ({min(count, 20)} of {count})"):
            st.dataframe(bad_rows.head(20), use_container_width=True)


def _render_date_gaps(df: pl.DataFrame) -> None:
    """Find and display missing calendar dates in the order data."""
    render_section_header("Date gaps", "📅")

    if "order_date" not in df.columns:
        st.info("No `order_date` column found in the data.")
        return

    date_min = df["order_date"].min()
    date_max = df["order_date"].max()

    if date_min is None or date_max is None:
        st.info("Cannot determine date range (min/max is null).")
        return

    # Build full calendar between min and max
    all_dates: set[date] = set()
    current = date_min
    while current <= date_max:
        all_dates.add(current)
        current += timedelta(days=1)

    actual_dates = set(df["order_date"].unique().to_list())
    missing_dates = sorted(all_dates - actual_dates)

    if len(missing_dates) == 0:
        st.success("Date gaps: 0 — all calendar days between min and max are covered")
    else:
        st.warning(f"Date gaps: {len(missing_dates)} missing calendar days")
        # Collect dates adjacent to each gap for context
        neighbor_dates: set[date] = set()
        for md in missing_dates:
            day_before = md - timedelta(days=1)
            day_after = md + timedelta(days=1)
            if day_before in actual_dates:
                neighbor_dates.add(day_before)
            if day_after in actual_dates:
                neighbor_dates.add(day_after)

        context_rows = df.filter(pl.col("order_date").is_in(sorted(neighbor_dates)))
        with st.expander(f"Show missing dates ({len(missing_dates)}) + surrounding rows"):
            if len(context_rows) > 0:
                st.caption("Rows from days adjacent to gaps (for locating in source file):")
                st.dataframe(context_rows.head(50), use_container_width=True)
    st.caption("Weekends and holidays may be intentional gaps — review in context.")


def _render_quantity_anomalies(df: pl.DataFrame) -> None:
    """Detect null/zero, negative, and statistical outlier quantities."""
    render_section_header("Quantity anomalies", "⚠️")

    if "quantity" not in df.columns:
        st.info("No `quantity` column found in the data.")
        return

    # 1. Null or zero
    null_zero_mask = df["quantity"].is_null() | (df["quantity"] == 0)
    null_zero = df.filter(null_zero_mask)
    nz_count = len(null_zero)

    if nz_count == 0:
        st.success("Null/zero quantities: 0")
    else:
        st.warning(f"Null/zero quantities: {nz_count} rows")
        with st.expander(f"Show sample rows ({min(nz_count, 20)} of {nz_count})"):
            st.dataframe(null_zero.head(20), use_container_width=True)

    # 2. Negative
    neg_mask = df["quantity"] < 0
    negatives = df.filter(neg_mask)
    neg_count = len(negatives)

    if neg_count == 0:
        st.success("Negative quantities: 0")
    else:
        st.warning(f"Negative quantities: {neg_count} rows (possible returns)")
        with st.expander(f"Show sample rows ({min(neg_count, 20)} of {neg_count})"):
            st.dataframe(negatives.head(20), use_container_width=True)

    # 3. Statistical outliers (mean + 3*std)
    qty_col = df["quantity"].drop_nulls().cast(pl.Float64)
    if len(qty_col) > 0:
        mean_val = qty_col.mean()
        std_val = qty_col.std()
        if mean_val is not None and std_val is not None and std_val > 0:
            threshold = mean_val + 3 * std_val
            outlier_mask = df["quantity"].cast(pl.Float64) > threshold
            outliers = df.filter(outlier_mask)
            out_count = len(outliers)

            if out_count == 0:
                st.success("Statistical outliers: 0")
            else:
                st.warning(
                    f"Statistical outliers: {out_count} rows with unusually high "
                    f"quantity (>{threshold:.0f})"
                )
                st.caption(
                    "Outliers detected using the 3-sigma rule: values exceeding "
                    "the average plus 3× standard deviation are flagged as extreme."
                )
                with st.expander(f"Show sample rows ({min(out_count, 20)} of {out_count})"):
                    st.dataframe(
                        outliers.sort("quantity", descending=True).head(20),
                        use_container_width=True,
                    )
        else:
            st.success("Statistical outliers: 0 (no variance)")


def _render_working_pattern(df: pl.DataFrame) -> None:
    """Show working pattern profile when hourly data is available."""
    has_hourly = "order_hour" in df.columns and df["order_hour"].n_unique() > 1
    if not has_hourly:
        return

    render_section_header("Working pattern profile", "🕐")

    # Active days per week
    day_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    if "weekday" in df.columns:
        active_weekdays = sorted(df["weekday"].unique().to_list())
        active_count = len(active_weekdays)
        day_labels = [day_names.get(d, str(d)) for d in active_weekdays]
        days_text = f"{day_labels[0]}-{day_labels[-1]}" if len(day_labels) > 1 else day_labels[0]
    elif "order_date" in df.columns:
        weekdays = df["order_date"].cast(pl.Date).dt.weekday().unique().drop_nulls().to_list()
        active_weekdays = sorted(weekdays)
        active_count = len(active_weekdays)
        day_labels = [day_names.get(d, str(d)) for d in active_weekdays]
        days_text = f"{day_labels[0]}-{day_labels[-1]}" if len(day_labels) > 1 else day_labels[0]
    else:
        active_count = df["order_date"].n_unique() if "order_date" in df.columns else 0
        days_text = str(active_count) if active_count else "unknown"

    # Active hours range — detect largest gap (handles overnight shifts)
    unique_hours = sorted(df["order_hour"].unique().drop_nulls().to_list())
    if len(unique_hours) >= 2:
        # Calculate gaps between consecutive hours (circular)
        gaps = []
        for i in range(len(unique_hours) - 1):
            gaps.append((unique_hours[i + 1] - unique_hours[i], i))
        # Wrap-around gap (last hour → first hour next day)
        gaps.append((24 - unique_hours[-1] + unique_hours[0], len(unique_hours) - 1))

        # Largest gap = inactive period
        largest_gap, gap_idx = max(gaps, key=lambda x: x[0])

        start_hour = unique_hours[(gap_idx + 1) % len(unique_hours)]
        end_hour = unique_hours[gap_idx]

        hours_text = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        span = (end_hour - start_hour) % 24 or 24
    elif len(unique_hours) == 1:
        hours_text = f"{unique_hours[0]:02d}:00"
        span = 1
    else:
        hours_text = "N/A"
        span = 0

    # Estimated shifts
    shifts = max(1, round(span / 8)) if span > 0 else 1

    col1, col2, col3 = st.columns(3)
    with col1:
        label = f"{days_text} → {active_count} days/week"
        st.metric("Active days per week", label)
    with col2:
        st.metric("Active hours range", hours_text)
    with col3:
        st.metric("Estimated shifts", f"~{shifts}")

    st.caption(
        "Working pattern is informational only — derived from order timestamps. "
        "Estimated shifts = active span / 8, rounded."
    )
