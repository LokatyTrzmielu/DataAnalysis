"""Main DataAnalysis Streamlit application.

Refactored to use modular views from src.ui.views package.
Each tab's content is rendered by a dedicated view module.
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
    page_title="DataAnalysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import views
from src.ui.views import (
    render_import_view,
    render_validation_view,
    render_capacity_view,
    render_performance_view,
    render_reports_view,
)
from src.ui.theme import apply_theme


def init_session_state() -> None:
    """Initialize session state with default values."""
    from src.core.carriers import CarrierService
    from src.core.config import OUTLIER_THRESHOLDS

    defaults = {
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
            }
            for c in carriers
        ]
        st.session_state.carriers_loaded = True


def render_sidebar() -> None:
    """Render sidebar with application parameters and status."""
    from src.core.config import OUTLIER_THRESHOLDS

    with st.sidebar:
        st.title("DataAnalysis")
        st.markdown("---")

        # Client name
        st.session_state.client_name = st.text_input(
            "Client name",
            value=st.session_state.client_name,
            placeholder="e.g. Client_ABC",
        )

        st.markdown("---")
        st.subheader("Analysis parameters")

        # Productive hours
        st.session_state.productive_hours = st.slider(
            "Productive hours / shift",
            min_value=4.0,
            max_value=8.0,
            value=7.0,
            step=0.5,
            help="Effective work time per shift",
        )

        # Borderline threshold
        st.session_state.borderline_threshold = st.slider(
            "Borderline threshold (mm)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Threshold for marking SKU as BORDERLINE (close to carrier limit)",
        )

        st.markdown("---")
        st.subheader("Imputation")

        st.session_state.imputation_enabled = st.checkbox(
            "Enable imputation",
            value=True,
            help="Fill missing values with selected method",
        )

        if st.session_state.imputation_enabled:
            st.session_state.imputation_method = st.selectbox(
                "Imputation method",
                options=["Median", "Average"],
                index=0,
                key="imputation_method_select",
                help="Median is more robust to outliers; Average uses arithmetic mean",
            )

        st.markdown("---")
        st.subheader("Outlier validation")

        st.session_state.outlier_validation_enabled = st.checkbox(
            "Enable outlier detection",
            value=True,
            help="Flag values outside acceptable ranges",
        )

        if st.session_state.outlier_validation_enabled:
            with st.expander("Outlier thresholds", expanded=False):
                st.markdown("**Dimensions (mm):**")
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.outlier_length_min = st.number_input(
                        "Length min", value=int(OUTLIER_THRESHOLDS["length_mm"]["min"]),
                        min_value=0, step=1, key="ol_len_min"
                    )
                    st.session_state.outlier_width_min = st.number_input(
                        "Width min", value=int(OUTLIER_THRESHOLDS["width_mm"]["min"]),
                        min_value=0, step=1, key="ol_wid_min"
                    )
                    st.session_state.outlier_height_min = st.number_input(
                        "Height min", value=int(OUTLIER_THRESHOLDS["height_mm"]["min"]),
                        min_value=0, step=1, key="ol_hgt_min"
                    )
                with col2:
                    st.session_state.outlier_length_max = st.number_input(
                        "Length max", value=int(OUTLIER_THRESHOLDS["length_mm"]["max"]),
                        min_value=1, step=100, key="ol_len_max"
                    )
                    st.session_state.outlier_width_max = st.number_input(
                        "Width max", value=int(OUTLIER_THRESHOLDS["width_mm"]["max"]),
                        min_value=1, step=100, key="ol_wid_max"
                    )
                    st.session_state.outlier_height_max = st.number_input(
                        "Height max", value=int(OUTLIER_THRESHOLDS["height_mm"]["max"]),
                        min_value=1, step=100, key="ol_hgt_max"
                    )

                st.markdown("**Weight (kg):**")
                col3, col4 = st.columns(2)
                with col3:
                    st.session_state.outlier_weight_min = st.number_input(
                        "Weight min", value=OUTLIER_THRESHOLDS["weight_kg"]["min"],
                        min_value=0.0, step=0.001, format="%.3f", key="ol_wgt_min"
                    )
                with col4:
                    st.session_state.outlier_weight_max = st.number_input(
                        "Weight max", value=OUTLIER_THRESHOLDS["weight_kg"]["max"],
                        min_value=0.1, step=10.0, key="ol_wgt_max"
                    )

        st.markdown("---")

        # Status badges
        if st.session_state.masterdata_df is not None:
            st.success(f"Masterdata: {len(st.session_state.masterdata_df)} SKU")
        if st.session_state.orders_df is not None:
            st.success(f"Orders: {len(st.session_state.orders_df)} lines")
        if st.session_state.analysis_complete:
            st.success("Analysis complete")


def render_tabs() -> None:
    """Render main application tabs.

    Tab structure:
    - Import: Data import with column mapping
    - Validation: Data quality checks
    - Capacity: Capacity analysis with carrier management
    - Performance: Performance analysis with shift configuration
    - Reports: Report generation and download
    """
    tabs = st.tabs([
        "📁 Import",
        "✅ Validation",
        "📊 Capacity",
        "⚡ Performance",
        "📄 Reports",
    ])

    with tabs[0]:
        render_import_view()

    with tabs[1]:
        render_validation_view()

    with tabs[2]:
        render_capacity_view()

    with tabs[3]:
        render_performance_view()

    with tabs[4]:
        render_reports_view()


def main() -> None:
    """Main application entry point."""
    # Apply custom dark theme
    apply_theme()

    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Render main tabs
    render_tabs()


if __name__ == "__main__":
    main()
