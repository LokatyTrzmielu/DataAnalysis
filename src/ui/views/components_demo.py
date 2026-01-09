"""Demo page for UI components - Etap 2 verification."""

from __future__ import annotations

import streamlit as st

from src.ui.layout import (
    get_status_color,
    render_card_container,
    render_centered_text,
    render_chart_container,
    render_divider,
    render_empty_state,
    render_error_box,
    render_info_box,
    render_kpi_card,
    render_kpi_section,
    render_message_box,
    render_metric_row,
    render_progress_section,
    render_section,
    render_section_header,
    render_spacer,
    render_status_badge,
    render_status_badges_inline,
    render_success_box,
    render_table_container,
    render_warning_box,
)
from src.ui.theme import COLORS, apply_theme


def render_demo_chart() -> None:
    """Render a simple demo chart using Plotly."""
    try:
        import plotly.graph_objects as go

        from src.ui.layout import apply_plotly_dark_theme

        fig = go.Figure(
            data=[
                go.Bar(
                    x=["A", "B", "C", "D"],
                    y=[10, 20, 15, 25],
                    marker_color=COLORS["primary"],
                )
            ]
        )
        apply_plotly_dark_theme(fig)
        fig.update_layout(height=250)
        st.plotly_chart(fig, width="stretch")
    except ImportError:
        st.warning("Plotly not installed. Run: pip install plotly")


def render_components_demo() -> None:
    """Render demo page showing all UI components."""
    apply_theme()

    st.title("UI Components Demo")
    st.caption("Etap 2 - Weryfikacja komponentow")

    render_divider()

    # Section 1: KPI Cards
    render_section_header("KPI Cards", icon="📊")

    st.markdown("**render_kpi_section() - 4 karty w rzedzie:**")
    render_kpi_section(
        [
            {
                "title": "Total SKU",
                "value": "1,234",
                "delta": "+12%",
                "delta_color": "positive",
                "icon": "📦",
            },
            {
                "title": "Fit Rate",
                "value": "87.5%",
                "delta": "+2.3%",
                "delta_color": "positive",
                "icon": "✅",
            },
            {
                "title": "Avg Weight",
                "value": "2.4 kg",
                "icon": "⚖️",
            },
            {
                "title": "Errors",
                "value": "3",
                "delta": "-5",
                "delta_color": "negative",
                "icon": "⚠️",
            },
        ]
    )

    render_spacer(20)

    st.markdown("**render_kpi_card() - pojedyncza karta:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi_card(
            title="Lines/Hour",
            value="156",
            delta="+8%",
            delta_color="positive",
            icon="⚡",
            help_text="Average lines processed per hour",
        )
    with col2:
        render_kpi_card(
            title="Orders",
            value="5,678",
            icon="📋",
        )
    with col3:
        render_kpi_card(
            title="Peak Hour",
            value="14:00",
            icon="🕐",
        )

    render_divider()

    # Section 2: Status Badges
    render_section_header("Status Badges", icon="🏷️")

    st.markdown("**render_status_badge() - pojedyncze badge:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_status_badge("Success", "success")
    with col2:
        render_status_badge("Warning", "warning")
    with col3:
        render_status_badge("Error", "error")
    with col4:
        render_status_badge("Info", "info")

    render_spacer(10)

    st.markdown("**render_status_badges_inline() - wiele badge w jednej linii:**")
    render_status_badges_inline(
        [
            ("Mapped: 45", "success"),
            ("Missing: 3", "error"),
            ("Pending: 12", "warning"),
        ]
    )

    render_divider()

    # Section 3: Message Boxes
    render_section_header("Message Boxes", icon="💬")

    render_info_box("This is an info message - useful for general information.")
    render_success_box("This is a success message - operation completed successfully!")
    render_warning_box("This is a warning message - please review before proceeding.")
    render_error_box("This is an error message - something went wrong.")

    render_divider()

    # Section 4: Sections & Containers
    render_section_header("Sections & Containers", icon="📁")

    st.markdown("**render_section() - collapsible section:**")
    with render_section("Collapsible Section Example", icon="📂", expanded=True):
        st.write("This content is inside a collapsible section.")
        st.write("Click the header to collapse/expand.")

    render_spacer(10)

    st.markdown("**render_card_container() - styled card:**")
    with render_card_container():
        st.write("This content is inside a styled card container.")
        st.write("Cards have consistent styling with hover effects.")

    render_divider()

    # Section 5: Charts
    render_section_header("Chart Container", icon="📈")

    st.markdown("**render_chart_container() - chart wrapper:**")
    render_chart_container(
        title="Sample Bar Chart",
        chart_func=render_demo_chart,
    )

    render_divider()

    # Section 6: Tables
    render_section_header("Table Container", icon="📋")

    st.markdown("**render_table_container() - styled table wrapper:**")
    with render_table_container(title="Sample Data Table"):
        import pandas as pd

        sample_data = pd.DataFrame(
            {
                "SKU": ["SKU-001", "SKU-002", "SKU-003"],
                "Length": [100, 150, 200],
                "Width": [50, 75, 100],
                "Height": [30, 40, 50],
                "Status": ["FIT", "BORDERLINE", "NOT_FIT"],
            }
        )
        st.dataframe(sample_data, width="stretch")

    render_divider()

    # Section 7: Utility Components
    render_section_header("Utility Components", icon="🔧")

    st.markdown("**render_metric_row() - native metrics:**")
    render_metric_row(
        [
            ("Metric 1", "100"),
            ("Metric 2", "200"),
            ("Metric 3", "300"),
        ]
    )

    render_spacer(20)

    st.markdown("**render_progress_section() - progress with label:**")
    render_progress_section(current=75, total=100, label="Processing")

    render_spacer(20)

    st.markdown("**render_centered_text() - centered text variants:**")
    render_centered_text("Small centered text", size="small")
    render_centered_text("Medium centered text", size="medium")
    render_centered_text("Large centered text", size="large")
    render_centered_text("Custom color text", size="medium", color=COLORS["primary"])

    render_divider()

    # Section 8: Empty State
    render_section_header("Empty State", icon="📭")

    st.markdown("**render_empty_state() - placeholder for empty data:**")
    with render_card_container():
        render_empty_state(
            message="No data available yet",
            icon="📊",
            action_label="Import Data",
        )

    render_divider()

    # Section 9: Colors Reference
    render_section_header("Color Palette Reference", icon="🎨")

    st.markdown("**COLORS dictionary values:**")
    color_cols = st.columns(5)
    for i, (name, hex_value) in enumerate(COLORS.items()):
        with color_cols[i % 5]:
            st.markdown(
                f'<div style="background-color: {hex_value}; padding: 1rem; '
                f'border-radius: 8px; margin-bottom: 0.5rem; text-align: center;">'
                f'<span style="color: {"#000" if name in ["text", "text_secondary"] else "#fff"};">'
                f"{name}</span></div>",
                unsafe_allow_html=True,
            )
            st.caption(hex_value)

    render_divider()

    st.success("All components rendered successfully!")


if __name__ == "__main__":
    render_components_demo()
