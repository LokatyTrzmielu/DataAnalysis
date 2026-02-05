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
    render_validation_view,
    render_capacity_view,
    render_performance_view,
    render_reports_view,
)
from src.ui.theme import apply_theme
from src.ui.layout import render_divider, render_sidebar_status_section

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
        # Active tab tracking for in_progress status
        "capacity_active_tab": "import",
        "performance_active_tab": "import",
        # Mapping history service (singleton)
        "mapping_history_service": None,
        # Custom carriers for capacity analysis
        "custom_carriers": [],
        # Outlier validation (simplified - carriers define limits)
        "outlier_validation_enabled": True,
        # Borderline threshold (used in Capacity Analysis)
        "borderline_threshold": 2.0,
        # Capacity DQ result (outliers/borderline detected in Capacity Analysis)
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

    Returns:
        List of step dicts with name, status, and detail fields.
        Status can be: "success", "in_progress", or "pending".
    """
    steps = []
    masterdata_df = st.session_state.get("masterdata_df")
    quality_result = st.session_state.get("quality_result")
    capacity_result = st.session_state.get("capacity_result")
    mapping_step = st.session_state.get("masterdata_mapping_step", "upload")
    active_tab = st.session_state.get("capacity_active_tab", "import")

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
    elif masterdata_df is not None and active_tab == "validation":
        steps.append({
            "name": "Validation",
            "status": "in_progress",
            "detail": "configuring...",
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
    elif quality_result is not None and active_tab == "analysis":
        steps.append({
            "name": "Analysis",
            "status": "in_progress",
            "detail": "configuring...",
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

    Returns:
        List of step dicts with name, status, and detail fields.
        Status can be: "success", "in_progress", or "pending".
    """
    steps = []
    orders_df = st.session_state.get("orders_df")
    performance_result = st.session_state.get("performance_result")
    mapping_step = st.session_state.get("orders_mapping_step", "upload")
    active_tab = st.session_state.get("performance_active_tab", "import")

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

    # Step 2: Validation
    if orders_df is not None and active_tab == "validation":
        steps.append({
            "name": "Validation",
            "status": "in_progress",
            "detail": "configuring...",
        })
    elif orders_df is not None:
        steps.append({
            "name": "Validation",
            "status": "success",
            "detail": "ready",
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
    elif orders_df is not None and active_tab == "analysis":
        steps.append({
            "name": "Analysis",
            "status": "in_progress",
            "detail": "configuring...",
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
    """Render Dashboard with status overview."""
    from src.ui.layout import render_kpi_card

    st.header("Dashboard")

    # Status cards - 4 columns
    cols = st.columns(4)

    with cols[0]:
        masterdata_count = len(st.session_state.masterdata_df) if st.session_state.masterdata_df is not None else 0
        value = f"{masterdata_count} SKU" if masterdata_count > 0 else "Not loaded"
        render_kpi_card("Masterdata", value)

    with cols[1]:
        orders_count = len(st.session_state.orders_df) if st.session_state.orders_df is not None else 0
        value = f"{orders_count} lines" if orders_count > 0 else "Not loaded"
        render_kpi_card("Orders", value)

    with cols[2]:
        capacity_done = st.session_state.capacity_result is not None
        value = "Complete" if capacity_done else "Pending"
        render_kpi_card("Capacity Analysis", value)

    with cols[3]:
        performance_done = st.session_state.performance_result is not None
        value = "Complete" if performance_done else "Pending"
        render_kpi_card("Performance Analysis", value)


def _render_capacity_section() -> None:
    """Render Capacity section with sub-tabs."""
    st.header("Capacity")
    tabs = st.tabs(["Import", "Validation", "Analysis"])

    with tabs[0]:
        st.session_state.capacity_active_tab = "import"
        _render_capacity_import()

    with tabs[1]:
        st.session_state.capacity_active_tab = "validation"
        _render_capacity_validation()

    with tabs[2]:
        st.session_state.capacity_active_tab = "analysis"
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
        col1, col2 = st.columns(2)

        with col1:
            # Client name
            st.session_state.client_name = st.text_input(
                "Client name",
                value=st.session_state.client_name,
                placeholder="e.g. Client_ABC",
            )

        with col2:
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

        st.caption("Outlier and Borderline detection is now configured in Analysis tab")

    render_divider()

    # Use existing validation view (without header, already shown above)
    render_validation_view(show_header=False)


def _render_performance_section() -> None:
    """Render Performance section with sub-tabs."""
    st.header("Performance")
    tabs = st.tabs(["Import", "Validation", "Analysis"])

    with tabs[0]:
        st.session_state.performance_active_tab = "import"
        _render_performance_import()

    with tabs[1]:
        st.session_state.performance_active_tab = "validation"
        _render_performance_validation()

    with tabs[2]:
        st.session_state.performance_active_tab = "analysis"
        render_performance_view()


def _render_performance_import() -> None:
    """Render Performance Import sub-tab (Orders only)."""
    # Use specific orders import function
    render_orders_import()


def _render_performance_validation() -> None:
    """Render Performance Validation sub-tab with settings."""
    from src.ui.layout import render_message_box

    st.header("✅ Validation")

    if st.session_state.orders_df is None:
        st.info("Import Orders in the Import tab first")
        return

    # Performance Settings section
    with st.expander("⚙️ Performance Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # Productive hours
            st.session_state.productive_hours = st.slider(
                "Productive hours / shift",
                min_value=4.0,
                max_value=8.0,
                value=st.session_state.get("productive_hours", 7.0),
                step=0.5,
                help="Effective work time per shift",
            )

        with col2:
            # Placeholder for future settings
            st.markdown("*Additional settings can be added here*")

    render_divider()

    # Use existing validation view (without header, already shown above)
    render_validation_view(show_header=False)


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
