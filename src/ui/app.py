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
from src.ui.layout import render_bold_label, render_divider

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
    from src.core.config import OUTLIER_THRESHOLDS

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
        # Outlier validation settings
        "outlier_validation_enabled": True,
        "outlier_length_min": OUTLIER_THRESHOLDS["length_mm"]["min"],
        "outlier_length_max": OUTLIER_THRESHOLDS["length_mm"]["max"],
        "outlier_width_min": OUTLIER_THRESHOLDS["width_mm"]["min"],
        "outlier_width_max": OUTLIER_THRESHOLDS["width_mm"]["max"],
        "outlier_height_min": OUTLIER_THRESHOLDS["height_mm"]["min"],
        "outlier_height_max": OUTLIER_THRESHOLDS["height_mm"]["max"],
        "outlier_weight_min": OUTLIER_THRESHOLDS["weight_kg"]["min"],
        "outlier_weight_max": OUTLIER_THRESHOLDS["weight_kg"]["max"],
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

        # Status badges (always visible)
        st.markdown("### Status")
        if st.session_state.masterdata_df is not None:
            st.markdown(f"✅ Masterdata: {len(st.session_state.masterdata_df)} SKU")
        else:
            st.markdown("ℹ️ Masterdata: Not loaded")
        if st.session_state.orders_df is not None:
            st.markdown(f"✅ Orders: {len(st.session_state.orders_df)} lines")
        else:
            st.markdown("ℹ️ Orders: Not loaded")
        if st.session_state.analysis_complete:
            st.markdown("✅ Analysis complete")


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
        # For now, render masterdata part of import view
        # Will be split in Etap 2
        _render_capacity_import()

    with tabs[1]:
        # For now, render masterdata validation
        # Will be split in Etap 2
        _render_capacity_validation()

    with tabs[2]:
        render_capacity_view()


def _render_capacity_import() -> None:
    """Render Capacity Import sub-tab (Masterdata only)."""
    # Use specific masterdata import function
    render_masterdata_import()


def _render_capacity_validation() -> None:
    """Render Capacity Validation sub-tab with settings."""
    from src.core.config import OUTLIER_THRESHOLDS
    from src.ui.layout import render_message_box

    st.header("✅ Validation")

    if st.session_state.masterdata_df is None:
        render_message_box("Please import Masterdata first in the Import tab.", "info")
        return

    # Capacity Settings section
    with st.expander("⚙️ Capacity Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # Client name
            st.session_state.client_name = st.text_input(
                "Client name",
                value=st.session_state.client_name,
                placeholder="e.g. Client_ABC",
            )

            # Borderline threshold
            st.session_state.borderline_threshold = st.slider(
                "Borderline threshold (mm)",
                min_value=0.5,
                max_value=10.0,
                value=st.session_state.get("borderline_threshold", 2.0),
                step=0.5,
                help="Threshold for marking SKU as BORDERLINE (close to carrier limit)",
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
                    help="Median is more robust to outliers",
                )

        # Outlier validation
        render_bold_label("Outlier validation", "⚠️")
        st.session_state.outlier_validation_enabled = st.checkbox(
            "Enable outlier detection",
            value=st.session_state.get("outlier_validation_enabled", True),
            help="Flag values outside acceptable ranges",
        )

        if st.session_state.outlier_validation_enabled:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.session_state.outlier_length_min = st.number_input(
                    "Length min (mm)",
                    value=float(st.session_state.get("outlier_length_min", OUTLIER_THRESHOLDS["length_mm"]["min"])),
                    min_value=0.0, step=0.001, format="%.3f", key="cv_ol_len_min"
                )
                st.session_state.outlier_length_max = st.number_input(
                    "Length max (mm)",
                    value=float(st.session_state.get("outlier_length_max", OUTLIER_THRESHOLDS["length_mm"]["max"])),
                    min_value=0.001, step=100.0, format="%.1f", key="cv_ol_len_max"
                )
            with col2:
                st.session_state.outlier_width_min = st.number_input(
                    "Width min (mm)",
                    value=float(st.session_state.get("outlier_width_min", OUTLIER_THRESHOLDS["width_mm"]["min"])),
                    min_value=0.0, step=0.001, format="%.3f", key="cv_ol_wid_min"
                )
                st.session_state.outlier_width_max = st.number_input(
                    "Width max (mm)",
                    value=float(st.session_state.get("outlier_width_max", OUTLIER_THRESHOLDS["width_mm"]["max"])),
                    min_value=0.001, step=100.0, format="%.1f", key="cv_ol_wid_max"
                )
            with col3:
                st.session_state.outlier_height_min = st.number_input(
                    "Height min (mm)",
                    value=float(st.session_state.get("outlier_height_min", OUTLIER_THRESHOLDS["height_mm"]["min"])),
                    min_value=0.0, step=0.001, format="%.3f", key="cv_ol_hgt_min"
                )
                st.session_state.outlier_height_max = st.number_input(
                    "Height max (mm)",
                    value=float(st.session_state.get("outlier_height_max", OUTLIER_THRESHOLDS["height_mm"]["max"])),
                    min_value=0.001, step=100.0, format="%.1f", key="cv_ol_hgt_max"
                )
            with col4:
                st.session_state.outlier_weight_min = st.number_input(
                    "Weight min (kg)",
                    value=float(st.session_state.get("outlier_weight_min", OUTLIER_THRESHOLDS["weight_kg"]["min"])),
                    min_value=0.0, step=0.001, format="%.3f", key="cv_ol_wgt_min"
                )
                st.session_state.outlier_weight_max = st.number_input(
                    "Weight max (kg)",
                    value=float(st.session_state.get("outlier_weight_max", OUTLIER_THRESHOLDS["weight_kg"]["max"])),
                    min_value=0.001, step=10.0, format="%.1f", key="cv_ol_wgt_max"
                )

    render_divider()

    # Use existing validation view (without header, already shown above)
    render_validation_view(show_header=False)


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
    """Render Performance Validation sub-tab with settings."""
    from src.ui.layout import render_message_box

    st.header("✅ Validation")

    if st.session_state.orders_df is None:
        render_message_box("Please import Orders first in the Import tab.", "info")
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
