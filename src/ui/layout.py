"""Reusable UI layout components for the Streamlit app."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, Literal

import streamlit as st

from src.ui.theme import COLORS, STATUS_COLORS, STATUS_ICONS

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


# Status type for new 7-type system
StatusType = Literal[
    "pending", "in_progress", "submitted", "in_review", "success", "failed", "expired"
]


def render_status_button(
    text: str,
    status: StatusType,
    show_icon: bool = True,
) -> None:
    """Render a status button with icon and appropriate color.

    Args:
        text: Button text
        status: Status type (one of 7 types)
        show_icon: Whether to show the SVG icon
    """
    icon_html = STATUS_ICONS.get(status, "") if show_icon else ""
    st.markdown(
        f'<span class="status-btn {status}">{icon_html}{text}</span>',
        unsafe_allow_html=True,
    )


def render_status_buttons_inline(
    buttons: list[tuple[str, StatusType]],
    show_icons: bool = True,
) -> None:
    """Render multiple status buttons inline.

    Args:
        buttons: List of (text, status) tuples
        show_icons: Whether to show SVG icons
    """
    buttons_html = " ".join(
        f'<span class="status-btn {status}">'
        f'{STATUS_ICONS.get(status, "") if show_icons else ""}{text}</span>'
        for text, status in buttons
    )
    st.markdown(buttons_html, unsafe_allow_html=True)


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


# ===== ETAP 2: Dodatkowe komponenty =====


def render_message_box(
    message: str,
    box_type: Literal["info", "warning", "error", "success"] = "info",
) -> None:
    """Render a styled message box.

    Args:
        message: Message text to display
        box_type: Type of box (determines color/style)
    """
    st.markdown(
        f'<div class="{box_type}-box"><p>{message}</p></div>',
        unsafe_allow_html=True,
    )


def render_info_box(message: str) -> None:
    """Render an info message box (blue accent)."""
    render_message_box(message, "info")


def render_warning_box(message: str) -> None:
    """Render a warning message box (orange accent)."""
    render_message_box(message, "warning")


def render_error_box(message: str) -> None:
    """Render an error message box (red accent)."""
    render_message_box(message, "error")


def render_success_box(message: str) -> None:
    """Render a success message box (green accent)."""
    render_message_box(message, "success")


@contextmanager
def render_table_container(title: str | None = None) -> Generator[None, None, None]:
    """Context manager for a styled table container.

    Args:
        title: Optional title for the table section

    Yields:
        None (content is rendered inside the container)
    """
    if title:
        st.markdown(
            f'<div class="table-container"><h4>{title}</h4>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_row(metrics: list[tuple[str, str | int | float]]) -> None:
    """Render a simple row of metrics using Streamlit's native metric component.

    Args:
        metrics: List of (label, value) tuples
    """
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value)


def render_divider() -> None:
    """Render a styled horizontal divider."""
    st.markdown(
        f'<hr style="border: none; border-top: 1px solid {COLORS["border"]}; margin: 1.5rem 0;">',
        unsafe_allow_html=True,
    )


def render_spacer(height: int = 20) -> None:
    """Render vertical space.

    Args:
        height: Height in pixels
    """
    st.markdown(f'<div style="height: {height}px;"></div>', unsafe_allow_html=True)


def render_centered_text(
    text: str,
    size: Literal["small", "medium", "large"] = "medium",
    color: str | None = None,
) -> None:
    """Render centered text.

    Args:
        text: Text to display
        size: Text size (small=0.85rem, medium=1rem, large=1.25rem)
        color: Optional color override (defaults to text_secondary)
    """
    sizes = {"small": "0.85rem", "medium": "1rem", "large": "1.25rem"}
    text_color = color or COLORS["text_secondary"]
    st.markdown(
        f'<p style="text-align: center; font-size: {sizes[size]}; color: {text_color};">{text}</p>',
        unsafe_allow_html=True,
    )


def render_empty_state(
    message: str,
    icon: str = "📭",
    action_label: str | None = None,
) -> bool:
    """Render an empty state placeholder with optional action button.

    Args:
        message: Message to display
        icon: Emoji icon to show
        action_label: Optional button label

    Returns:
        True if action button was clicked, False otherwise
    """
    st.markdown(
        f"""
        <div style="text-align: center; padding: 3rem; color: {COLORS["text_secondary"]};">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
            <p style="font-size: 1.1rem; margin: 0;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if action_label:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            return st.button(action_label, width="stretch")
    return False


def render_progress_section(
    current: int,
    total: int,
    label: str = "Progress",
) -> None:
    """Render a progress indicator with label.

    Args:
        current: Current value
        total: Total value
        label: Label text
    """
    progress = current / total if total > 0 else 0
    percentage = int(progress * 100)
    st.markdown(
        f'<p style="color: {COLORS["text_secondary"]}; margin-bottom: 0.5rem;">'
        f"{label}: {current}/{total} ({percentage}%)</p>",
        unsafe_allow_html=True,
    )
    st.progress(progress)


def get_status_color(
    status: Literal[
        "success", "warning", "error", "info",
        "pending", "in_progress", "submitted", "in_review", "failed", "expired"
    ]
) -> str:
    """Get the color for a given status.

    Args:
        status: Status type (supports both legacy 4-type and new 7-type system)

    Returns:
        Hex color string
    """
    # New 7-type system
    if status in STATUS_COLORS:
        return STATUS_COLORS[status]

    # Legacy mapping
    legacy_colors = {
        "success": STATUS_COLORS["success"],
        "warning": STATUS_COLORS["pending"],
        "error": STATUS_COLORS["failed"],
        "info": STATUS_COLORS["in_progress"],
    }
    return legacy_colors.get(status, COLORS["text_secondary"])


def render_navigation_buttons(
    show_back: bool = True,
    show_next: bool = True,
    back_label: str = "< Back",
    next_label: str = "Next >",
    on_back: Callable[[], None] | None = None,
    on_next: Callable[[], None] | None = None,
    next_disabled: bool = False,
    back_disabled: bool = False,
) -> tuple[bool, bool]:
    """Render navigation buttons at the bottom of a view.

    Args:
        show_back: Whether to show the back button
        show_next: Whether to show the next button
        back_label: Label for back button
        next_label: Label for next button
        on_back: Callback when back is clicked
        on_next: Callback when next is clicked
        next_disabled: Disable the next button
        back_disabled: Disable the back button

    Returns:
        Tuple of (back_clicked, next_clicked) booleans
    """
    st.markdown("---")

    back_clicked = False
    next_clicked = False

    cols = st.columns([1, 2, 1])

    with cols[0]:
        if show_back:
            if st.button(
                back_label,
                key="nav_back",
                use_container_width=True,
                disabled=back_disabled,
            ):
                back_clicked = True
                if on_back:
                    on_back()

    with cols[2]:
        if show_next:
            if st.button(
                next_label,
                key="nav_next",
                use_container_width=True,
                disabled=next_disabled,
                type="primary",
            ):
                next_clicked = True
                if on_next:
                    on_next()

    return back_clicked, next_clicked
