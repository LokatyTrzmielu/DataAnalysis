"""UI module - Streamlit app + pages."""

from src.ui.theme import COLORS, apply_theme, get_custom_css
from src.ui.layout import (
    render_kpi_card,
    render_kpi_section,
    render_section_header,
    render_section,
    render_status_badge,
    render_status_badges_inline,
    render_card_container,
    render_chart_container,
    get_plotly_layout_defaults,
    apply_plotly_dark_theme,
)

__all__ = [
    "COLORS",
    "apply_theme",
    "get_custom_css",
    "render_kpi_card",
    "render_kpi_section",
    "render_section_header",
    "render_section",
    "render_status_badge",
    "render_status_badges_inline",
    "render_card_container",
    "render_chart_container",
    "get_plotly_layout_defaults",
    "apply_plotly_dark_theme",
]
