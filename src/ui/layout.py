"""Reusable UI layout components for the Streamlit app."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, Literal

import streamlit as st

from src.ui.theme import COLORS

if TYPE_CHECKING:
    from collections.abc import Generator


def render_kpi_card(
    title: str,
    value: str | int | float,
    delta: str | None = None,
    delta_color: Literal["positive", "negative", "neutral"] = "positive",
    icon: str | None = None,
    help_text: str | None = None,
) -> None:
    """Render a KPI card with value and optional delta.

    Args:
        title: Card title (displayed as label)
        value: Main value to display
        delta: Optional change indicator
        delta_color: Color for delta (positive=green, negative=red, neutral=gray)
        icon: Optional emoji icon
        help_text: Optional tooltip text
    """
    delta_class = delta_color if delta else ""
    icon_html = f'<span class="icon">{icon}</span>' if icon else ""
    delta_html = f'<p class="delta {delta_class}">{delta}</p>' if delta else ""

    card_html = f"""
    <div class="kpi-card">
        <h3>{icon_html}{title}</h3>
        <p class="value">{value}</p>
        {delta_html}
    </div>
    """

    if help_text:
        st.markdown(card_html, unsafe_allow_html=True, help=help_text)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def render_kpi_section(metrics: list[dict]) -> None:
    """Render a row of KPI cards.

    Args:
        metrics: List of dicts with keys: title, value, delta (optional),
                 delta_color (optional), icon (optional), help_text (optional)
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            render_kpi_card(
                title=metric["title"],
                value=metric["value"],
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "positive"),
                icon=metric.get("icon"),
                help_text=metric.get("help_text"),
            )


def render_section_header(title: str, icon: str | None = None) -> None:
    """Render a section header with optional icon.

    Args:
        title: Section title
        icon: Optional emoji icon
    """
    icon_html = f'<span class="icon">{icon}</span>' if icon else ""
    st.markdown(
        f'<div class="section-header">{icon_html}{title}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def render_section(
    title: str,
    icon: str | None = None,
    expanded: bool = True,
) -> Generator[None, None, None]:
    """Context manager for a collapsible section with header.

    Args:
        title: Section title
        icon: Optional emoji icon
        expanded: Whether section is expanded by default

    Yields:
        None (content is rendered inside the context)
    """
    label = f"{icon} {title}" if icon else title
    with st.expander(label, expanded=expanded):
        yield


def render_status_badge(
    text: str,
    status: Literal["success", "warning", "error", "info"],
) -> None:
    """Render a status badge with appropriate color.

    Args:
        text: Badge text
        status: Status type (determines color)
    """
    st.markdown(
        f'<span class="status-badge {status}">{text}</span>',
        unsafe_allow_html=True,
    )


def render_status_badges_inline(badges: list[tuple[str, str]]) -> None:
    """Render multiple status badges inline.

    Args:
        badges: List of (text, status) tuples
    """
    badges_html = " ".join(
        f'<span class="status-badge {status}">{text}</span>'
        for text, status in badges
    )
    st.markdown(badges_html, unsafe_allow_html=True)


@contextmanager
def render_card_container() -> Generator[None, None, None]:
    """Context manager for a styled card container.

    Yields:
        None (content is rendered inside the container)
    """
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    yield
    st.markdown('</div>', unsafe_allow_html=True)


def render_chart_container(
    title: str,
    chart_func: Callable[..., None],
    **chart_kwargs,
) -> None:
    """Wrapper for Plotly charts with title.

    Args:
        title: Chart title
        chart_func: Function that renders the chart
        **chart_kwargs: Keyword arguments passed to chart_func
    """
    st.markdown(
        f'<div class="chart-container"><h4>{title}</h4>',
        unsafe_allow_html=True,
    )
    chart_func(**chart_kwargs)
    st.markdown('</div>', unsafe_allow_html=True)


def get_plotly_layout_defaults() -> dict:
    """Return default Plotly layout settings for dark theme.

    Returns:
        Dict with Plotly layout configuration
    """
    return {
        "paper_bgcolor": COLORS["surface"],
        "plot_bgcolor": COLORS["surface"],
        "font": {"color": COLORS["text"]},
        "xaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": COLORS["text"]},
        },
        "margin": {"l": 40, "r": 40, "t": 40, "b": 40},
    }


def apply_plotly_dark_theme(fig) -> None:
    """Apply dark theme to a Plotly figure.

    Args:
        fig: Plotly figure object to modify in-place
    """
    fig.update_layout(**get_plotly_layout_defaults())
