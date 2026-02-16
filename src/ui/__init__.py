"""UI module - Streamlit app + pages."""

from src.ui.theme import COLORS, STATUS_COLORS, STATUS_ICONS, apply_theme, get_custom_css
from src.ui.layout import (
    render_kpi_card,
    render_kpi_section,
    render_section_header,
    render_section,
    render_status_badge,
    render_status_badges_inline,
    render_status_button,
    render_status_buttons_inline,
    render_card_container,
    render_chart_container,
    get_plotly_layout_defaults,
    apply_plotly_theme,
)

__all__ = [
    "COLORS",
    "STATUS_COLORS",
    "STATUS_ICONS",
    "apply_theme",
    "get_custom_css",
    "render_kpi_card",
    "render_kpi_section",
    "render_section_header",
    "render_section",
    "render_status_badge",
    "render_status_badges_inline",
    "render_status_button",
    "render_status_buttons_inline",
    "render_card_container",
    "render_chart_container",
    "get_plotly_layout_defaults",
    "apply_plotly_theme",
]
