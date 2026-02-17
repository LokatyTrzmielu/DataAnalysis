"""Reusable UI layout components for the Streamlit app."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, Literal

import streamlit as st

from src.ui.theme import COLORS, STATUS_COLORS, STATUS_ICONS

# Pipeline status type
PipelineStatusType = Literal["pending", "success", "in_progress", "failed"]

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

    parts = [
        '<div class="kpi-card">',
        f'<h3>{icon_html}{title}</h3>',
        f'<p class="value">{value}</p>',
    ]
    if delta:
        parts.append(f'<p class="delta {delta_class}">{delta}</p>')
    if help_text:
        parts.append(f'<p class="help-text">{help_text}</p>')
    parts.append("</div>")

    st.markdown("\n".join(parts), unsafe_allow_html=True)


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


# DEPRECATED - use render_status_button() instead (7-type system)
def render_status_badge(
    text: str,
    status: Literal["success", "warning", "error", "info"],
) -> None:
    """Render a status badge with appropriate color.

    DEPRECATED: Use render_status_button() with 7-type status system instead.
    This function uses legacy 4-type status system (success/warning/error/info).

    Args:
        text: Badge text
        status: Status type (determines color)
    """
    st.markdown(
        f'<span class="status-badge {status}">{text}</span>',
        unsafe_allow_html=True,
    )


# DEPRECATED - use render_status_buttons_inline() instead (7-type system)
def render_status_badges_inline(badges: list[tuple[str, str]]) -> None:
    """Render multiple status badges inline.

    DEPRECATED: Use render_status_buttons_inline() with 7-type status system instead.
    This function uses legacy 4-type status system (success/warning/error/info).

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
    """Return default Plotly layout settings for light theme.

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
        "height": 400,
    }


def apply_plotly_theme(fig) -> None:
    """Apply theme to a Plotly figure.

    Args:
        fig: Plotly figure object to modify in-place
    """
    fig.update_layout(**get_plotly_layout_defaults())


def render_plotly_chart(fig, filename: str, **kwargs) -> None:
    """Render Plotly chart with custom PNG export filename.

    Args:
        fig: Plotly figure object
        filename: Base filename (without extension) for the PNG download
        **kwargs: Additional arguments passed to st.plotly_chart
    """
    config = {
        "toImageButtonOptions": {
            "filename": filename,
            "format": "png",
        }
    }
    st.plotly_chart(fig, config=config, **kwargs)


def render_chart_download_button(fig, filename: str) -> None:
    """Render a download button for an interactive HTML version of a Plotly chart.

    Args:
        fig: Plotly figure object
        filename: Base filename (without extension) for the downloaded file
    """
    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    st.download_button(
        label="📥 Download interactive HTML",
        data=html,
        file_name=f"{filename}.html",
        mime="text/html",
        key=f"dl_{filename}",
    )


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


def render_forward_guidance(message: str) -> None:
    """Render a forward guidance banner directing user to next step.

    Args:
        message: Guidance text (e.g. "Proceed to the Validation tab")
    """
    st.markdown(
        f'<div class="forward-guidance"><span class="arrow">&#10132;</span> {message}</div>',
        unsafe_allow_html=True,
    )


def render_alert_banner(
    title: str,
    message: str,
    severity: Literal["critical", "warning", "info"] = "warning",
) -> None:
    """Render an alert banner for threshold violations or important findings.

    Args:
        title: Short alert title (e.g. "Low Fit Rate")
        message: Detailed alert description
        severity: Alert severity (critical=red, warning=amber, info=blue)
    """
    severity_config = {
        "critical": {"bg": "#fde8e8", "border": COLORS["error"], "icon": "&#9888;", "title_color": COLORS["error"]},
        "warning": {"bg": "#fef3cd", "border": COLORS["warning"], "icon": "&#9888;", "title_color": COLORS["warning"]},
        "info": {"bg": "#e8f0fe", "border": STATUS_COLORS["in_progress"], "icon": "&#8505;", "title_color": STATUS_COLORS["in_progress"]},
    }
    cfg = severity_config.get(severity, severity_config["warning"])
    st.markdown(
        f'<div style="background:{cfg["bg"]}; border-left: 4px solid {cfg["border"]}; '
        f'border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.75rem;">'
        f'<strong style="color:{cfg["title_color"]};">{cfg["icon"]} {title}</strong>'
        f'<p style="color:{COLORS["text"]}; margin: 0.25rem 0 0 0; font-size: 0.9rem;">{message}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_alerts_from_data() -> None:
    """Check analysis results and render alert banners for threshold violations.

    Checks:
    - Capacity: fit rate < 70% (warning), < 50% (critical)
    - Capacity: not-fit SKU > 10% (warning), > 25% (critical)
    - Performance: P95 throughput very high vs avg (warning if > 3x)
    """
    alerts: list[tuple[str, str, str]] = []  # (title, message, severity)

    # --- Capacity alerts ---
    capacity_result = st.session_state.get("capacity_result")
    if capacity_result is not None:
        # Average fit rate across carriers
        fit_rates = []
        for cid, stats in capacity_result.carrier_stats.items():
            if cid != "NONE":
                fit_rates.append(stats.fit_percentage)

        if fit_rates:
            avg_fit = sum(fit_rates) / len(fit_rates)
            if avg_fit < 50:
                alerts.append((
                    "Low Fit Rate",
                    f"Average fit rate is {avg_fit:.1f}% — less than half of SKU fit the carriers. "
                    "Consider adding larger carriers or reviewing SKU dimensions.",
                    "critical",
                ))
            elif avg_fit < 70:
                alerts.append((
                    "Below Target Fit Rate",
                    f"Average fit rate is {avg_fit:.1f}% — below the 70% target. "
                    "Some carriers may be undersized for the product mix.",
                    "warning",
                ))

        # Not-fit SKU in prioritized/best-fit mode
        none_stats = capacity_result.carrier_stats.get("NONE")
        if none_stats and capacity_result.total_sku > 0:
            not_fit_pct = none_stats.not_fit_count / capacity_result.total_sku * 100
            if not_fit_pct > 25:
                alerts.append((
                    "High Not-Fit Rate",
                    f"{none_stats.not_fit_count} SKU ({not_fit_pct:.0f}%) don't fit any carrier.",
                    "critical",
                ))
            elif not_fit_pct > 10:
                alerts.append((
                    "Notable Not-Fit Rate",
                    f"{none_stats.not_fit_count} SKU ({not_fit_pct:.0f}%) don't fit any carrier.",
                    "warning",
                ))

    # --- Performance alerts ---
    perf_result = st.session_state.get("performance_result")
    if perf_result is not None:
        kpi = perf_result.kpi
        if perf_result.has_hourly_data and kpi.avg_lines_per_hour > 0:
            peak_ratio = kpi.p95_lines_per_hour / kpi.avg_lines_per_hour
            if peak_ratio > 3.0:
                alerts.append((
                    "High Peak Variability",
                    f"P95 throughput ({kpi.p95_lines_per_hour:.0f} lines/h) is {peak_ratio:.1f}x "
                    f"the average ({kpi.avg_lines_per_hour:.0f} lines/h). "
                    "Consider peak staffing or load balancing.",
                    "warning",
                ))

    # Render all alerts
    for title, message, severity in alerts:
        render_alert_banner(title, message, severity)


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


# ===== ETAP 3: Nowe komponenty =====


def render_bold_label(
    text: str,
    icon: str | None = None,
    size: Literal["small", "medium", "large"] = "medium",
) -> None:
    """Render a styled bold label with optional icon.

    Use this instead of st.markdown("**text**") for consistent styling.

    Args:
        text: Label text to display
        icon: Optional emoji icon (displayed before text)
        size: Text size (small=0.9rem, medium=1rem, large=1.1rem)
    """
    sizes = {"small": "0.9rem", "medium": "1rem", "large": "1.1rem"}
    icon_html = f'<span style="margin-right: 0.4rem;">{icon}</span>' if icon else ""
    st.markdown(
        f'<p style="font-weight: 600; font-size: {sizes[size]}; color: {COLORS["text"]}; '
        f'margin: 0.5rem 0;">{icon_html}{text}</p>',
        unsafe_allow_html=True,
    )


def render_data_table(
    df,
    height: int = 400,
    title: str | None = None,
    hide_index: bool = True,
) -> None:
    """Render a styled dataframe table with consistent settings.

    Args:
        df: Polars or Pandas DataFrame to display
        height: Table height in pixels (default 400)
        title: Optional title displayed above the table
        hide_index: Whether to hide the row index (default True)
    """
    if title:
        st.markdown(
            f'<p style="font-weight: 600; font-size: 1rem; color: {COLORS["text"]}; '
            f'margin-bottom: 0.5rem;">{title}</p>',
            unsafe_allow_html=True,
        )

    st.dataframe(
        df,
        height=height,
        hide_index=hide_index,
        use_container_width=True,
    )


# ===== Sidebar Pipeline Status Components =====


def render_sidebar_status_indicator(status: PipelineStatusType) -> str:
    """Return HTML for pipeline circle indicator.

    Args:
        status: One of pending, success, in_progress, failed

    Returns:
        HTML string for the indicator circle
    """
    return f'<div class="pipeline-indicator {status}"></div>'


def render_sidebar_pipeline_step(
    name: str,
    status: PipelineStatusType,
    detail: str | None = None,
    is_last: bool = False,
) -> str:
    """Render a single pipeline step with connector line.

    Args:
        name: Step name (e.g., "Masterdata", "Validation")
        status: Step status (pending, success, in_progress, failed)
        detail: Optional detail text (e.g., "1,234 SKU loaded")
        is_last: Whether this is the last step (no connector line after)

    Returns:
        HTML string for the pipeline step
    """
    connector_class = "connector-success" if status == "success" else ""
    indicator_html = render_sidebar_status_indicator(status)
    detail_html = f'<div class="pipeline-step-detail">{detail}</div>' if detail else ""

    return (
        f'<div class="pipeline-step {connector_class}">'
        f'{indicator_html}'
        f'<div class="pipeline-step-content">'
        f'<div class="pipeline-step-name">{name}</div>'
        f'{detail_html}'
        f'</div>'
        f'</div>'
    )


def render_sidebar_status_section(
    title: str,
    steps: list[dict],
    icon: str | None = None,
) -> None:
    """Render a status section (Capacity/Performance) with pipeline steps.

    Args:
        title: Section title (e.g., "CAPACITY", "PERFORMANCE")
        steps: List of step dicts with keys: name, status, detail (optional)
               Example: [{"name": "Masterdata", "status": "success", "detail": "1,234 SKU"}]
        icon: Optional emoji icon for the section
    """
    icon_html = f'<span class="section-icon">{icon}</span>' if icon else ""

    steps_html = ""
    for i, step in enumerate(steps):
        is_last = i == len(steps) - 1
        steps_html += render_sidebar_pipeline_step(
            name=step["name"],
            status=step.get("status", "pending"),
            detail=step.get("detail"),
            is_last=is_last,
        )

    html = (
        f'<div class="sidebar-status-section">'
        f'<div class="section-title">{icon_html}{title}</div>'
        f'<div class="sidebar-pipeline">{steps_html}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
