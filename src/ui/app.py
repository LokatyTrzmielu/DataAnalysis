"""Main DataAnalysis Streamlit application.

Refactored to use modular views from src.ui.views package.
Hierarchical navigation with sidebar sections and sub-tabs.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root directory to PYTHONPATH
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import views
from src.ui.views import (
    render_import_view,
    render_masterdata_import,
    render_orders_import,
    render_capacity_validation_view,
    render_performance_validation_view,
    render_capacity_view,
    render_performance_view,
    render_reports_view,
)
from src.ui.theme import apply_theme, COLORS
from src.ui.layout import render_divider, render_sidebar_status_section, render_alerts_from_data

# Navigation constants
SECTIONS = {
    "Dashboard": "Dashboard",
    "Capacity": "Capacity",
    "Performance": "Performance",
    "Reports": "Reports",
}
SUBTAB_ORDER = ["import", "validation", "analysis"]


def init_session_state() -> None:
    """Initialize session state with default values."""
    from src.core.carriers import CarrierService

    defaults = {
        # Navigation state
        "active_section": "Dashboard",
        "active_subtab": "import",
        # Data state
        "client_name": "",
        "masterdata_df": None,
        "orders_df": None,
        "quality_result": None,
        "capacity_result": None,
        "performance_result": None,
        "current_step": 0,
        "analysis_complete": False,
        # Masterdata mapping state
        "masterdata_file_columns": None,
        "masterdata_mapping_result": None,
        "masterdata_original_mapping": None,
        "masterdata_temp_path": None,
        "masterdata_mapping_step": "upload",
        # Orders mapping state
        "orders_file_columns": None,
        "orders_mapping_result": None,
        "orders_original_mapping": None,
        "orders_temp_path": None,
        "orders_mapping_step": "upload",
        # Mapping history service (singleton)
        "mapping_history_service": None,
        # Custom carriers for capacity analysis
        "custom_carriers": [],
        # Borderline threshold (used in Capacity Analysis)
        "borderline_threshold": 2.0,
        # Capacity DQ result (generated during analysis for reports)
        "capacity_dq_result": None,
        # Carriers loaded flag
        "carriers_loaded": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize mapping history service
    if st.session_state.mapping_history_service is None:
        from src.ingest import MappingHistoryService
        st.session_state.mapping_history_service = MappingHistoryService()

    # Load carriers from file on first run
    if not st.session_state.carriers_loaded:
        service = CarrierService()
        carriers = service.load_all_carriers()
        st.session_state.custom_carriers = [
            {
                "carrier_id": c.carrier_id,
                "name": c.name,
                "inner_length_mm": c.inner_length_mm,
                "inner_width_mm": c.inner_width_mm,
                "inner_height_mm": c.inner_height_mm,
                "max_weight_kg": c.max_weight_kg,
                "is_predefined": c.is_predefined,
                "is_active": c.is_active,
                "priority": c.priority,
            }
            for c in carriers
        ]
        st.session_state.carriers_loaded = True


def get_capacity_status() -> list[dict]:
    """Calculate capacity pipeline status from session_state.

    Status is based on actual data state, not which tab is active.

    Returns:
        List of step dicts with name, status, and detail fields.
        Status can be: "success", "in_progress", or "pending".
    """
    steps = []
    masterdata_df = st.session_state.get("masterdata_df")
    quality_result = st.session_state.get("quality_result")
    capacity_result = st.session_state.get("capacity_result")
    mapping_step = st.session_state.get("masterdata_mapping_step", "upload")

    # Step 1: Masterdata
    if masterdata_df is not None:
        count = len(masterdata_df)
        steps.append({
            "name": "Masterdata",
            "status": "success",
            "detail": f"{count:,} SKU loaded",
        })
    elif mapping_step == "mapping":
        steps.append({
            "name": "Masterdata",
            "status": "in_progress",
            "detail": "mapping...",
        })
    else:
        steps.append({
            "name": "Masterdata",
            "status": "pending",
            "detail": "pending",
        })

    # Step 2: Validation
    if quality_result is not None:
        steps.append({
            "name": "Validation",
            "status": "success",
            "detail": "complete",
        })
    elif masterdata_df is not None:
        steps.append({
            "name": "Validation",
            "status": "pending",
            "detail": "ready",
        })
    else:
        steps.append({
            "name": "Validation",
            "status": "pending",
            "detail": "pending",
        })

    # Step 3: Analysis
    if capacity_result is not None:
        steps.append({
            "name": "Analysis",
            "status": "success",
            "detail": "complete",
        })
    elif quality_result is not None:
        steps.append({
            "name": "Analysis",
            "status": "pending",
            "detail": "ready",
        })
    else:
        steps.append({
            "name": "Analysis",
            "status": "pending",
            "detail": "pending",
        })

    return steps


def get_performance_status() -> list[dict]:
    """Calculate performance pipeline status from session_state.

    Performance has its own independent pipeline, separate from Capacity.
    Status is based on actual data state, not which tab is active.

    Returns:
        List of step dicts with name, status, and detail fields.
        Status can be: "success", "in_progress", or "pending".
    """
    steps = []
    orders_df = st.session_state.get("orders_df")
    performance_result = st.session_state.get("performance_result")
    mapping_step = st.session_state.get("orders_mapping_step", "upload")

    # Step 1: Orders
    if orders_df is not None:
        count = len(orders_df)
        steps.append({
            "name": "Orders",
            "status": "success",
            "detail": f"{count:,} lines loaded",
        })
    elif mapping_step == "mapping":
        steps.append({
            "name": "Orders",
            "status": "in_progress",
            "detail": "mapping...",
        })
    else:
        steps.append({
            "name": "Orders",
            "status": "pending",
            "detail": "pending",
        })

    # Step 2: Validation (auto-validated on import for performance)
    if orders_df is not None:
        steps.append({
            "name": "Validation",
            "status": "success",
            "detail": "auto-validated",
        })
    else:
        steps.append({
            "name": "Validation",
            "status": "pending",
            "detail": "pending",
        })

    # Step 3: Analysis
    if performance_result is not None:
        steps.append({
            "name": "Analysis",
            "status": "success",
            "detail": "complete",
        })
    elif orders_df is not None:
        steps.append({
            "name": "Analysis",
            "status": "pending",
            "detail": "ready",
        })
    else:
        steps.append({
            "name": "Analysis",
            "status": "pending",
            "detail": "pending",
        })

    return steps


def render_sidebar_status() -> None:
    """Render both Capacity and Performance pipeline status sections."""
    # Capacity pipeline
    capacity_steps = get_capacity_status()
    render_sidebar_status_section("CAPACITY", capacity_steps, icon="📦")

    # Performance pipeline
    performance_steps = get_performance_status()
    render_sidebar_status_section("PERFORMANCE", performance_steps, icon="📈")


def render_sidebar() -> None:
    """Render sidebar with navigation."""
    with st.sidebar:
        st.title("Data Analysis")
        render_divider()

        # Section navigation
        st.markdown("### Navigation")

        # Get current section key for radio
        current_key = next(
            (k for k, v in SECTIONS.items() if v == st.session_state.active_section),
            "🏠 Dashboard"
        )

        selected = st.radio(
            "Section",
            list(SECTIONS.keys()),
            index=list(SECTIONS.keys()).index(current_key),
            label_visibility="collapsed",
            key="section_nav"
        )
        st.session_state.active_section = SECTIONS[selected]

        render_divider()

        # Client name (visible from all sections, used in Reports)
        st.session_state.client_name = st.text_input(
            "Client name",
            value=st.session_state.client_name,
            placeholder="e.g. Client_ABC",
            key="sidebar_client_name",
        )

        render_divider()

        # Pipeline status sections
        st.markdown("### Status")
        render_sidebar_status()


def render_main_content() -> None:
    """Render main content based on active section.

    Section structure:
    - Dashboard: Status overview
    - Capacity: [Import] [Validation] [Analysis] sub-tabs
    - Performance: [Import] [Validation] [Analysis] sub-tabs
    - Reports: Report generation
    """
    section = st.session_state.active_section

    if section == "Dashboard":
        _render_dashboard()
    elif section == "Capacity":
        _render_capacity_section()
    elif section == "Performance":
        _render_performance_section()
    elif section == "Reports":
        _render_reports_section()


def _render_dashboard() -> None:
    """Render Dashboard with status overview and real KPIs after analysis."""
    from src.ui.layout import render_kpi_card, render_kpi_section, render_divider, render_section_header

    st.header("Dashboard")

    has_masterdata = st.session_state.masterdata_df is not None
    has_orders = st.session_state.orders_df is not None
    has_capacity = st.session_state.capacity_result is not None
    has_performance = st.session_state.performance_result is not None
    has_any_data = has_masterdata or has_orders

    # Getting Started guidance when no data loaded
    if not has_any_data:
        st.markdown(
            f"""
            <div style="background-color: {COLORS["surface_elevated"]}; border: 1px solid {COLORS["accent_muted"]};
                        border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h3 style="color: {COLORS["text"]}; margin-top: 0;">Getting Started</h3>
                <p style="color: {COLORS["text_secondary"]}; margin-bottom: 1rem;">
                    Follow these steps to analyze your warehouse data:
                </p>
                <ol style="color: {COLORS["text"]}; line-height: 2;">
                    <li><strong>Capacity</strong> &rarr; Import tab &rarr; Upload Masterdata file (SKU dimensions & weights)</li>
                    <li><strong>Capacity</strong> &rarr; Validation tab &rarr; Validate and clean data quality</li>
                    <li><strong>Capacity</strong> &rarr; Analysis tab &rarr; Run capacity analysis against carriers</li>
                    <li><strong>Performance</strong> &rarr; Import tab &rarr; Upload Orders file (optional)</li>
                    <li><strong>Reports</strong> &rarr; Download all generated reports</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # --- Data loaded: show pipeline status KPIs ---
    render_section_header("Data Overview", "📋")

    overview_metrics = []

    # Masterdata
    if has_masterdata:
        masterdata_count = len(st.session_state.masterdata_df)
        overview_metrics.append({
            "title": "Masterdata",
            "value": f"{masterdata_count:,} SKU",
            "icon": "📦",
        })
    else:
        overview_metrics.append({"title": "Masterdata", "value": "Not loaded", "icon": "📦"})

    # Validation
    has_validation = st.session_state.quality_result is not None
    if has_validation:
        overview_metrics.append({"title": "Validation", "value": "Complete", "icon": "✅"})
    elif has_masterdata:
        overview_metrics.append({"title": "Validation", "value": "Ready", "icon": "⏳"})

    # Orders
    if has_orders:
        orders_count = len(st.session_state.orders_df)
        overview_metrics.append({
            "title": "Orders",
            "value": f"{orders_count:,} lines",
            "icon": "📋",
        })
    else:
        overview_metrics.append({"title": "Orders", "value": "Not loaded", "icon": "📋"})

    # Analysis status
    if has_capacity and has_performance:
        overview_metrics.append({"title": "Analysis", "value": "Both complete", "icon": "✅"})
    elif has_capacity:
        overview_metrics.append({"title": "Analysis", "value": "Capacity done", "icon": "📊"})
    elif has_performance:
        overview_metrics.append({"title": "Analysis", "value": "Performance done", "icon": "📈"})

    render_kpi_section(overview_metrics)

    # --- Alerts (when any analysis complete) ---
    if has_capacity or has_performance:
        render_divider()
        render_alerts_from_data()

    # --- Capacity KPIs (when analysis complete) ---
    if has_capacity:
        _render_dashboard_capacity_kpis()

    # --- Performance KPIs (when analysis complete) ---
    if has_performance:
        render_divider()
        _render_dashboard_performance_kpis()

    # --- Executive Summary (when both analyses complete) ---
    if has_capacity or has_performance:
        render_divider()
        _render_executive_summary(has_capacity, has_performance)


def _render_dashboard_capacity_kpis() -> None:
    """Render capacity analysis KPIs on dashboard."""
    from src.ui.layout import render_kpi_section, render_section_header

    import polars as pl

    result = st.session_state.capacity_result
    df = st.session_state.masterdata_df

    render_section_header("Capacity Analysis", "📦")

    # Average fit % across carriers (excluding NONE)
    fit_percentages = []
    for carrier_id, stats in result.carrier_stats.items():
        if carrier_id != "NONE":
            fit_percentages.append(stats.fit_percentage)
    avg_fit_pct = sum(fit_percentages) / len(fit_percentages) if fit_percentages else 0

    # Count carriers analyzed (excluding NONE)
    carriers_count = sum(1 for cid in result.carriers_analyzed if cid != "NONE")

    # Not-fit count (in prioritized/best-fit mode)
    none_stats = result.carrier_stats.get("NONE")
    not_fit_count = none_stats.not_fit_count if none_stats else 0

    # Average dimensions
    avg_length = df.select(pl.col("length_mm").mean()).item() or 0
    avg_width = df.select(pl.col("width_mm").mean()).item() or 0
    avg_weight = df.select(pl.col("weight_kg").mean()).item() or 0

    metrics = [
        {
            "title": "SKU Analyzed",
            "value": f"{result.total_sku:,}",
            "help_text": "Total SKU in capacity analysis",
        },
        {
            "title": "Avg Fit Rate",
            "value": f"{avg_fit_pct:.1f}%",
            "help_text": f"Average fit % across {carriers_count} carrier(s)",
        },
        {
            "title": "Carriers",
            "value": str(carriers_count),
            "help_text": "Number of carriers analyzed",
        },
        {
            "title": "Avg Weight",
            "value": f"{avg_weight:.1f} kg",
            "help_text": "Average SKU weight",
        },
    ]

    # Replace last metric with not-fit count if relevant
    if not_fit_count > 0:
        metrics[3] = {
            "title": "Not Fitting",
            "value": f"{not_fit_count}",
            "help_text": "SKU not fitting any carrier",
            "delta": f"{not_fit_count / result.total_sku * 100:.1f}% of total",
            "delta_color": "negative",
        }

    render_kpi_section(metrics)


def _render_dashboard_performance_kpis() -> None:
    """Render performance analysis KPIs on dashboard."""
    from src.ui.layout import render_kpi_section, render_section_header

    result = st.session_state.performance_result
    kpi = result.kpi

    render_section_header("Performance Analysis", "📈")

    metrics = [
        {
            "title": "Total Orders",
            "value": f"{kpi.total_orders:,}",
            "help_text": "Total unique orders",
        },
        {
            "title": "Total Lines",
            "value": f"{kpi.total_lines:,}",
            "help_text": "Total order lines",
        },
        {
            "title": "Avg Lines/Order",
            "value": f"{kpi.avg_lines_per_order:.1f}",
            "help_text": "Average lines per order",
        },
    ]

    # Add hourly KPI if available
    if result.has_hourly_data:
        metrics.append({
            "title": "Avg Lines/Hour",
            "value": f"{kpi.avg_lines_per_hour:.0f}",
            "help_text": "Average throughput per hour",
        })
    else:
        metrics.append({
            "title": "Unique SKU",
            "value": f"{kpi.unique_sku:,}",
            "help_text": "Unique SKU in orders",
        })

    render_kpi_section(metrics)


def _render_executive_summary(has_capacity: bool, has_performance: bool) -> None:
    """Render executive summary combining insights from all analyses.

    Args:
        has_capacity: Whether capacity analysis is available
        has_performance: Whether performance analysis is available
    """
    from src.ui.insights import (
        generate_capacity_insights,
        generate_performance_insights,
        render_insights,
    )
    from src.ui.layout import render_section_header

    render_section_header("Executive Summary", "📋")

    all_insights = []

    if has_capacity:
        all_insights.extend(generate_capacity_insights())

    if has_performance:
        all_insights.extend(generate_performance_insights())

    if all_insights:
        # Sort: warnings first, then info, then positive
        priority = {"warning": 0, "info": 1, "positive": 2}
        all_insights.sort(key=lambda i: priority.get(i.type, 3))
        render_insights(all_insights, title="All Findings")
    else:
        st.info("Run analyses to see findings here.")


def _render_capacity_section() -> None:
    """Render Capacity section with sub-tabs."""
    st.header("Capacity")
    tabs = st.tabs(["Import", "Validation", "Analysis"])

    with tabs[0]:
        _render_capacity_import()

    with tabs[1]:
        _render_capacity_validation()

    with tabs[2]:
        render_capacity_view()


def _render_capacity_import() -> None:
    """Render Capacity Import sub-tab (Masterdata only)."""
    # Use specific masterdata import function
    render_masterdata_import()


def _render_capacity_validation() -> None:
    """Render Capacity Validation sub-tab with settings."""
    st.header("✅ Validation")

    if st.session_state.masterdata_df is None:
        st.info("Import Masterdata in the Import tab first")
        return

    # Validation Settings section (simplified - outliers moved to Capacity Analysis)
    with st.expander("⚙️ Validation Settings", expanded=False):
        # Imputation
        st.session_state.imputation_enabled = st.checkbox(
            "Enable imputation",
            value=st.session_state.get("imputation_enabled", True),
            help="Fill missing values with selected method",
        )

        if st.session_state.imputation_enabled:
            st.session_state.imputation_method = st.selectbox(
                "Imputation method",
                options=["Median", "Average"],
                index=0 if st.session_state.get("imputation_method", "Median") == "Median" else 1,
                key="capacity_imputation_method_select",
                help=(
                    "Median: Each field (length, width, height, weight, quantity) gets its own "
                    "global median calculated from all valid values in the dataset. "
                    "Values ≤0 and null are treated as missing and replaced with this median. "
                    "More robust to outliers.\n\n"
                    "Average: Each field gets its own global mean calculated from all valid values. "
                    "Values ≤0 and null are treated as missing and replaced with this average. "
                    "More sensitive to extreme values."
                ),
            )

        st.caption("Outliers (SKUs not fitting any carrier) are detected automatically during analysis")

    render_divider()

    # Use existing capacity validation view (without header, already shown above)
    render_capacity_validation_view(show_header=False)


def _render_performance_section() -> None:
    """Render Performance section with sub-tabs."""
    st.header("Performance")
    tabs = st.tabs(["Import", "Validation", "Analysis"])

    with tabs[0]:
        _render_performance_import()

    with tabs[1]:
        _render_performance_validation()

    with tabs[2]:
        render_performance_view()


def _render_performance_import() -> None:
    """Render Performance Import sub-tab (Orders only)."""
    # Use specific orders import function
    render_orders_import()


def _render_performance_validation() -> None:
    """Render Performance Validation sub-tab."""
    st.header("✅ Validation")

    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    # Use performance-specific validation view
    render_performance_validation_view()


def _render_reports_section() -> None:
    """Render Reports section."""
    render_reports_view()


def main() -> None:
    """Main application entry point."""
    # Apply custom dark theme
    apply_theme()

    # Initialize session state
    init_session_state()

    # Render sidebar with navigation
    render_sidebar()

    # Render main content based on active section
    render_main_content()


if __name__ == "__main__":
    main()
