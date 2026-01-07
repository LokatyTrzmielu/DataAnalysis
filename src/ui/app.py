"""Main DataAnalysis Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from src.ingest import MappingResult

# Add project root directory to PYTHONPATH
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="DataAnalysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialize session state."""
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
        "masterdata_original_mapping": None,  # For tracking corrections
        "masterdata_temp_path": None,
        "masterdata_mapping_step": "upload",
        # Orders mapping state
        "orders_file_columns": None,
        "orders_mapping_result": None,
        "orders_original_mapping": None,  # For tracking corrections
        "orders_temp_path": None,
        "orders_mapping_step": "upload",
        # Mapping history service (singleton)
        "mapping_history_service": None,
        # Custom carriers for capacity analysis
        "custom_carriers": [],
        # Outlier validation settings - use unified thresholds from config
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
    """Render sidebar with parameters."""
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

        # Utilization - DISABLED
        # st.session_state.utilization_vlm = st.slider(
        #     "Utilization VLM",
        #     min_value=0.5,
        #     max_value=1.0,
        #     value=0.75,
        #     step=0.05,
        #     help="Utilization coefficient for Vertical Lift Module",
        # )
        #
        # st.session_state.utilization_mib = st.slider(
        #     "Utilization MiB",
        #     min_value=0.5,
        #     max_value=1.0,
        #     value=0.68,
        #     step=0.05,
        #     help="Utilization coefficient for Mini-load in Box",
        # )

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

        # Status
        if st.session_state.masterdata_df is not None:
            st.success(f"Masterdata: {len(st.session_state.masterdata_df)} SKU")
        if st.session_state.orders_df is not None:
            st.success(f"Orders: {len(st.session_state.orders_df)} lines")
        if st.session_state.analysis_complete:
            st.success("Analysis complete")


def render_tabs() -> None:
    """Render main tabs."""
    tabs = st.tabs(["📁 Import", "✅ Validation", "📊 Analysis", "📄 Reports"])

    with tabs[0]:
        render_import_tab()

    with tabs[1]:
        render_validation_tab()

    with tabs[2]:
        render_analysis_tab()

    with tabs[3]:
        render_reports_tab()


def build_mapping_result_from_selections(
    user_mappings: dict[str, str],
    file_columns: list[str],
    schema: dict,
    original_mapping: "MappingResult | None" = None,
) -> "MappingResult":
    """Build MappingResult from user selections.

    Args:
        user_mappings: Dictionary target_field -> source_column
        file_columns: All columns from file
        schema: MASTERDATA_SCHEMA or ORDERS_SCHEMA
        original_mapping: Original auto-mapping result to preserve is_auto status

    Returns:
        MappingResult
    """
    from src.ingest import MappingResult, ColumnMapping

    mappings = {}
    used_columns = set()

    for field_name, source_col in user_mappings.items():
        # Check if selection matches original auto-mapping
        original = original_mapping.mappings.get(field_name) if original_mapping else None
        if original and original.source_column == source_col:
            # User didn't change - preserve original is_auto and confidence
            mappings[field_name] = ColumnMapping(
                target_field=field_name,
                source_column=source_col,
                confidence=original.confidence,
                is_auto=original.is_auto,
            )
        else:
            # User changed selection - mark as manual
            mappings[field_name] = ColumnMapping(
                target_field=field_name,
                source_column=source_col,
                confidence=1.0,
                is_auto=False,
            )
        used_columns.add(source_col)

    # Determine missing required fields
    missing_required = []
    for field_name, field_cfg in schema.items():
        if field_cfg["required"] and field_name not in user_mappings:
            missing_required.append(field_name)

    # Unmapped columns
    unmapped_columns = [c for c in file_columns if c not in used_columns]

    return MappingResult(
        mappings=mappings,
        unmapped_columns=unmapped_columns,
        missing_required=missing_required,
    )


def _get_field_status_html(is_mapped: bool) -> str:
    """Return HTML for field status indicator with colored background.

    Args:
        is_mapped: Whether this field has a column mapped to it

    Returns:
        HTML string for the status indicator
    """
    if is_mapped:
        # Green - field is mapped
        return """<div style="background-color: #d4edda; padding: 6px 10px;
                  border-radius: 4px; border-left: 4px solid #28a745; margin-bottom: 4px;">
                  <small style="color: #155724;">✓ Done</small></div>"""
    else:
        # Red - field is not mapped
        return """<div style="background-color: #f8d7da; padding: 6px 10px;
                  border-radius: 4px; border-left: 4px solid #dc3545; margin-bottom: 4px;">
                  <small style="color: #721c24;">⚠ Missing</small></div>"""


def render_mapping_ui(
    file_columns: list[str],
    mapping_result: "MappingResult",
    schema: dict,
    key_prefix: str = "md",
) -> "MappingResult":
    """Render column mapping UI.

    Args:
        file_columns: Columns from loaded file
        mapping_result: Auto-mapping result
        schema: MASTERDATA_SCHEMA or ORDERS_SCHEMA
        key_prefix: Prefix for widget keys

    Returns:
        Updated MappingResult with user selections
    """
    st.subheader("Column mapping")

    # Get required fields only
    required_fields = [f for f, cfg in schema.items() if cfg["required"]]

    # Dropdown options: none + columns from file
    dropdown_options = ["-- Don't map --"] + list(file_columns)

    user_mappings = {}

    # Progress bar for required fields mapping
    # Calculate based on CURRENT session state widget values for accurate real-time update
    mapped_required = 0
    for field_name in required_fields:
        widget_key = f"{key_prefix}_map_{field_name}"
        current_selection = st.session_state.get(widget_key)
        if current_selection is not None and current_selection != "-- Don't map --":
            mapped_required += 1
        elif current_selection is None:
            # Fallback to auto-mapping if widget not yet rendered
            if mapping_result.mappings.get(field_name):
                mapped_required += 1

    total_required = len(required_fields)
    st.progress(
        mapped_required / total_required if total_required > 0 else 0,
        text=f"Required: {mapped_required}/{total_required} mapped",
    )

    # Required fields section - vertical layout
    for field_name in required_fields:
        field_cfg = schema[field_name]
        widget_key = f"{key_prefix}_map_{field_name}"

        # Get current mapping from auto-mapping result
        current_mapping = mapping_result.mappings.get(field_name)
        current_value = current_mapping.source_column if current_mapping else None

        # Find index for default selection
        if current_value and current_value in file_columns:
            default_idx = file_columns.index(current_value) + 1
        else:
            default_idx = 0

        # Check if field is currently mapped (from session state if available)
        current_selection = st.session_state.get(widget_key)
        is_mapped = current_selection is not None and current_selection != "-- Don't map --"
        # Fallback to auto-mapping if no session state yet
        if current_selection is None:
            is_mapped = current_value is not None

        # Row layout: status | field name | dropdown
        col_status, col_dropdown = st.columns([1, 4])

        with col_status:
            st.markdown(
                _get_field_status_html(is_mapped),
                unsafe_allow_html=True,
            )

        with col_dropdown:
            selected = st.selectbox(
                field_name,
                options=dropdown_options,
                index=default_idx,
                key=widget_key,
                help=field_cfg["description"],
            )

            if selected != "-- Don't map --":
                user_mappings[field_name] = selected

    # Build updated MappingResult
    return build_mapping_result_from_selections(user_mappings, file_columns, schema, mapping_result)


def render_mapping_status(mapping_result: MappingResult) -> bool:
    """Display mapping status and validation messages.

    Args:
        mapping_result: Current mapping result

    Returns:
        True if mapping has errors (missing required or duplicates)
    """
    has_errors = not mapping_result.is_complete

    # Check for duplicate column selections
    source_columns = [m.source_column for m in mapping_result.mappings.values()]
    duplicates = [col for col in set(source_columns) if source_columns.count(col) > 1]
    if duplicates:
        dup_fields = []
        for field_name, col_mapping in mapping_result.mappings.items():
            if col_mapping.source_column in duplicates:
                dup_fields.append(f"{field_name} <- `{col_mapping.source_column}`")
        # Vertical list for duplicates
        st.error("Duplicate column mappings:")
        for dup in dup_fields:
            st.markdown(f"• {dup}")
        has_errors = True

    # Mapping summary
    with st.expander("Mapping summary", expanded=False):
        for field_name, col_mapping in mapping_result.mappings.items():
            source = col_mapping.source_column
            auto_label = "auto" if col_mapping.is_auto else "manual"
            st.write(f"- **{field_name}** <- `{source}` ({auto_label})")

    # Unmapped columns in separate expander for cleaner display
    if mapping_result.unmapped_columns:
        count = len(mapping_result.unmapped_columns)
        with st.expander(f"ℹ️ {count} unmapped columns from file"):
            for col in mapping_result.unmapped_columns:
                st.text(f"• {col}")

    return has_errors


def render_masterdata_import() -> None:
    """Import Masterdata with mapping step."""
    import tempfile
    from src.ingest import (
        FileReader,
        MASTERDATA_SCHEMA,
        create_masterdata_wizard,
        MasterdataIngestPipeline,
    )
    from src.ingest.units import WeightUnit

    history_service = st.session_state.mapping_history_service

    st.subheader("Masterdata")

    step = st.session_state.get("masterdata_mapping_step", "upload")

    # Step 1: File upload
    if step == "upload":
        masterdata_file = st.file_uploader(
            "Select Masterdata file",
            type=["xlsx", "csv", "txt"],
            key="masterdata_upload",
        )

        if masterdata_file is not None:
            if st.button("Next - Column mapping", key="md_to_mapping"):
                with st.spinner("Analyzing file..."):
                    try:
                        # Save to temporary file
                        suffix = Path(masterdata_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(masterdata_file.read())
                            tmp_path = tmp.name

                        # Load columns and run auto-mapping
                        reader = FileReader(tmp_path)
                        columns = reader.get_columns()

                        wizard = create_masterdata_wizard(history_service)
                        client_name = st.session_state.get("client_name", "")
                        auto_mapping = wizard.auto_map(columns, client_name)

                        # Save in session state
                        st.session_state.masterdata_temp_path = tmp_path
                        st.session_state.masterdata_file_columns = columns
                        st.session_state.masterdata_mapping_result = auto_mapping
                        st.session_state.masterdata_original_mapping = auto_mapping
                        st.session_state.masterdata_mapping_step = "mapping"
                        st.rerun()

                    except Exception as e:
                        st.error(f"File analysis error: {e}")

    # Step 2: Column mapping
    elif step == "mapping":
        columns = st.session_state.masterdata_file_columns
        mapping = st.session_state.masterdata_mapping_result

        # Data preview
        with st.expander("Data preview", expanded=False):
            from src.ingest import FileReader
            reader = FileReader(st.session_state.masterdata_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), width='stretch')

        # Mapping UI
        updated_mapping = render_mapping_ui(
            file_columns=columns,
            mapping_result=mapping,
            schema=MASTERDATA_SCHEMA,
            key_prefix="md",
        )

        # Save updated mapping
        st.session_state.masterdata_mapping_result = updated_mapping

        # Status
        has_mapping_errors = render_mapping_status(updated_mapping)

        # Weight unit selection
        weight_unit_option = st.selectbox(
            "Weight unit in source file",
            options=["Auto-detect", "Grams (g)", "Kilograms (kg)"],
            index=0,
            key="md_weight_unit",
            help="Select unit if auto-detection fails for light items",
        )

        # Action buttons - Back on left, Import on right
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])

        with btn_col1:
            if st.button("Back", key="md_back_to_upload"):
                st.session_state.masterdata_mapping_step = "upload"
                st.session_state.masterdata_file_columns = None
                st.session_state.masterdata_mapping_result = None
                st.rerun()

        with btn_col3:
            import_disabled = not updated_mapping.is_complete or has_mapping_errors
            if st.button(
                "Import Masterdata",
                key="md_do_import",
                disabled=import_disabled,
                type="primary",
            ):
                with st.spinner("Importing..."):
                    try:
                        # Map weight unit selection
                        weight_unit_map = {
                            "Auto-detect": None,
                            "Grams (g)": WeightUnit.G,
                            "Kilograms (kg)": WeightUnit.KG,
                        }
                        selected_weight_unit = weight_unit_map.get(weight_unit_option)

                        pipeline = MasterdataIngestPipeline(
                            weight_unit=selected_weight_unit,
                        )
                        result = pipeline.run(
                            st.session_state.masterdata_temp_path,
                            mapping=updated_mapping,
                        )

                        st.session_state.masterdata_df = result.df
                        st.session_state.masterdata_mapping_step = "complete"

                        # Record user corrections to history
                        original = st.session_state.masterdata_original_mapping
                        if original is not None and history_service is not None:
                            wizard = create_masterdata_wizard(history_service)
                            client_name = st.session_state.get("client_name", "")
                            wizard.record_user_corrections(
                                original, updated_mapping, client_name
                            )
                            history_service.save_history()

                        st.success(f"Imported {result.rows_imported} rows")

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        st.rerun()

                    except Exception as e:
                        st.error(f"Import error: {e}")

    # Step 3: Import complete
    elif step == "complete":
        if st.session_state.masterdata_df is not None:
            st.success(f"Masterdata: {len(st.session_state.masterdata_df)} SKU")

            with st.expander("Data preview", expanded=False):
                st.dataframe(
                    st.session_state.masterdata_df.head(20).to_pandas(),
                    width='stretch'
                )

        if st.button("Import new file", key="md_new_import"):
            st.session_state.masterdata_mapping_step = "upload"
            st.session_state.masterdata_file_columns = None
            st.session_state.masterdata_mapping_result = None
            st.session_state.masterdata_temp_path = None
            st.session_state.masterdata_df = None
            st.rerun()


def render_orders_import() -> None:
    """Import Orders with mapping step."""
    import tempfile
    from src.ingest import (
        FileReader,
        ORDERS_SCHEMA,
        create_orders_wizard,
        OrdersIngestPipeline,
    )

    history_service = st.session_state.mapping_history_service

    st.subheader("Orders")

    step = st.session_state.get("orders_mapping_step", "upload")

    # Step 1: File upload
    if step == "upload":
        orders_file = st.file_uploader(
            "Select Orders file",
            type=["xlsx", "csv", "txt"],
            key="orders_upload",
        )

        if orders_file is not None:
            if st.button("Next - Column mapping", key="orders_to_mapping"):
                with st.spinner("Analyzing file..."):
                    try:
                        # Save to temporary file
                        suffix = Path(orders_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(orders_file.read())
                            tmp_path = tmp.name

                        # Load columns and run auto-mapping
                        reader = FileReader(tmp_path)
                        columns = reader.get_columns()

                        wizard = create_orders_wizard(history_service)
                        client_name = st.session_state.get("client_name", "")
                        auto_mapping = wizard.auto_map(columns, client_name)

                        # Save in session state
                        st.session_state.orders_temp_path = tmp_path
                        st.session_state.orders_file_columns = columns
                        st.session_state.orders_mapping_result = auto_mapping
                        st.session_state.orders_original_mapping = auto_mapping
                        st.session_state.orders_mapping_step = "mapping"
                        st.rerun()

                    except Exception as e:
                        st.error(f"File analysis error: {e}")

    # Step 2: Column mapping
    elif step == "mapping":
        columns = st.session_state.orders_file_columns
        mapping = st.session_state.orders_mapping_result

        # Data preview
        with st.expander("Data preview", expanded=False):
            from src.ingest import FileReader
            reader = FileReader(st.session_state.orders_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), width='stretch')

        # Mapping UI
        updated_mapping = render_mapping_ui(
            file_columns=columns,
            mapping_result=mapping,
            schema=ORDERS_SCHEMA,
            key_prefix="orders",
        )

        # Save updated mapping
        st.session_state.orders_mapping_result = updated_mapping

        # Status
        has_mapping_errors = render_mapping_status(updated_mapping)

        # Action buttons - Back on left, Import on right
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])

        with btn_col1:
            if st.button("Back", key="orders_back_to_upload"):
                st.session_state.orders_mapping_step = "upload"
                st.session_state.orders_file_columns = None
                st.session_state.orders_mapping_result = None
                st.rerun()

        with btn_col3:
            import_disabled = not updated_mapping.is_complete or has_mapping_errors
            if st.button(
                "Import Orders",
                key="orders_do_import",
                disabled=import_disabled,
                type="primary",
            ):
                with st.spinner("Importing..."):
                    try:
                        pipeline = OrdersIngestPipeline()
                        result = pipeline.run(
                            st.session_state.orders_temp_path,
                            mapping=updated_mapping,
                        )

                        st.session_state.orders_df = result.df
                        st.session_state.orders_mapping_step = "complete"

                        # Record user corrections to history
                        original = st.session_state.orders_original_mapping
                        if original is not None and history_service is not None:
                            wizard = create_orders_wizard(history_service)
                            client_name = st.session_state.get("client_name", "")
                            wizard.record_user_corrections(
                                original, updated_mapping, client_name
                            )
                            history_service.save_history()

                        st.success(f"Imported {result.rows_imported} rows")

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        st.rerun()

                    except Exception as e:
                        st.error(f"Import error: {e}")

    # Step 3: Import complete
    elif step == "complete":
        if st.session_state.orders_df is not None:
            st.success(f"Orders: {len(st.session_state.orders_df)} lines")

            with st.expander("Data preview", expanded=False):
                st.dataframe(
                    st.session_state.orders_df.head(20).to_pandas(),
                    width='stretch'
                )

        if st.button("Import new file", key="orders_new_import"):
            st.session_state.orders_mapping_step = "upload"
            st.session_state.orders_file_columns = None
            st.session_state.orders_mapping_result = None
            st.session_state.orders_temp_path = None
            st.session_state.orders_df = None
            st.rerun()


def render_import_tab() -> None:
    """Import tab."""
    st.header("Data import")

    col1, col2 = st.columns(2)

    with col1:
        render_masterdata_import()

    with col2:
        render_orders_import()


def render_validation_tab() -> None:
    """Validation tab."""
    st.header("Validation and data quality")

    if st.session_state.masterdata_df is None:
        st.info("First import Masterdata in the Import tab")
        return

    if st.button("Run validation", key="run_validation"):
        with st.spinner("Validation in progress..."):
            try:
                from src.quality import run_quality_pipeline
                from src.quality.impute import ImputationMethod

                # Build outlier thresholds from session state
                outlier_thresholds = {
                    "length_mm": {
                        "min": st.session_state.get("outlier_length_min", 1),
                        "max": st.session_state.get("outlier_length_max", 3000),
                    },
                    "width_mm": {
                        "min": st.session_state.get("outlier_width_min", 1),
                        "max": st.session_state.get("outlier_width_max", 3000),
                    },
                    "height_mm": {
                        "min": st.session_state.get("outlier_height_min", 1),
                        "max": st.session_state.get("outlier_height_max", 2000),
                    },
                    "weight_kg": {
                        "min": st.session_state.get("outlier_weight_min", 0.001),
                        "max": st.session_state.get("outlier_weight_max", 500.0),
                    },
                }

                # Determine imputation method
                imputation_method_str = st.session_state.get("imputation_method", "Median")
                imputation_method = (
                    ImputationMethod.MEAN if imputation_method_str == "Average"
                    else ImputationMethod.MEDIAN
                )

                result = run_quality_pipeline(
                    st.session_state.masterdata_df,
                    enable_imputation=st.session_state.get("imputation_enabled", True),
                    imputation_method=imputation_method,
                    enable_outlier_validation=st.session_state.get("outlier_validation_enabled", True),
                    outlier_thresholds=outlier_thresholds,
                )
                st.session_state.quality_result = result
                st.session_state.masterdata_df = result.df

                st.success("Validation complete")

            except Exception as e:
                st.error(f"Validation error: {e}")

    # Display results
    if st.session_state.quality_result is not None:
        result = st.session_state.quality_result

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Quality Score",
                f"{result.quality_score:.1f}%",
                help=(
                    "Weighted average of data coverage: dimensions (40%), weight (30%), "
                    "stock (30%), minus penalty for detected issues (0.5 point per issue, max 30). "
                    "Higher score indicates better data quality."
                ),
            )
        with col2:
            st.metric("Records", result.total_records)
        with col3:
            st.metric("Valid", result.valid_records)
        with col4:
            st.metric("Imputed", result.imputed_records)

        st.markdown("---")

        # Coverage
        st.subheader("Data coverage")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Before imputation:**")
            st.progress(result.metrics_before.dimensions_coverage_pct / 100,
                       text=f"Dimensions: {result.metrics_before.dimensions_coverage_pct:.1f}%")
            st.progress(result.metrics_before.weight_coverage_pct / 100,
                       text=f"Weight: {result.metrics_before.weight_coverage_pct:.1f}%")

        with col2:
            st.write("**After imputation:**")
            st.progress(result.metrics_after.dimensions_coverage_pct / 100,
                       text=f"Dimensions: {result.metrics_after.dimensions_coverage_pct:.1f}%")
            st.progress(result.metrics_after.weight_coverage_pct / 100,
                       text=f"Weight: {result.metrics_after.weight_coverage_pct:.1f}%")

        # Issues
        st.subheader("Detected issues")
        dq = result.dq_lists
        # Show 0 for Outliers/Borderline when validation is disabled
        outliers_count = (
            len(dq.suspect_outliers)
            if st.session_state.get("outlier_validation_enabled", True)
            else 0
        )
        borderline_count = (
            len(dq.high_risk_borderline)
            if st.session_state.get("borderline_threshold", 0) > 0
            else 0
        )
        problems = {
            "Missing Critical": len(dq.missing_critical),
            "Outliers": outliers_count,
            "Borderline": borderline_count,
            "Duplicates": len(dq.duplicates),
            "Conflicts": len(dq.conflicts),
        }

        for name, count in problems.items():
            if count > 0:
                st.warning(f"{name}: {count}")
            else:
                st.success(f"{name}: 0")

        # Validation help section
        with st.expander("Validation help", expanded=False):
            st.markdown("""
**Missing Critical** - Required fields (SKU, dimensions, weight) with missing or zero values.
These SKUs cannot be analyzed until the data is corrected.

**Outliers** - Values outside the acceptable range defined in settings.
Very small or very large dimensions/weights that may indicate data entry errors.
These SKUs are **excluded from capacity analysis** and listed for verification only.

**Borderline** - SKUs with dimensions very close to carrier size limits.
These items may have fitting issues during automated storage operations.
These SKUs are **excluded from capacity analysis** and listed for verification only.

**Duplicates** - Same SKU appearing multiple times in the masterdata.
Each SKU should appear only once with consistent dimension data.

**Conflicts** - Same SKU with different dimension or weight values across records.
Indicates inconsistent data that needs to be resolved.
            """)


def render_carrier_form() -> None:
    """Form for adding a new carrier."""
    st.markdown("**Add new carrier:**")

    with st.form("add_carrier_form", clear_on_submit=True):
        st.markdown("**Internal dimensions (mm):**")
        col_w, col_l, col_h = st.columns(3)
        with col_w:
            width_mm = st.number_input(
                "Width (W)",
                min_value=1,
                value=400,
                step=10,
                help="Internal width in mm",
            )
        with col_l:
            length_mm = st.number_input(
                "Length (L)",
                min_value=1,
                value=600,
                step=10,
                help="Internal length in mm",
            )
        with col_h:
            height_mm = st.number_input(
                "Height (H)",
                min_value=1,
                value=200,
                step=10,
                help="Internal height in mm",
            )

        max_weight = st.number_input(
            "Max weight (kg)",
            min_value=1,
            value=100,
            step=5,
            help="Maximum allowed load weight in kg",
        )

        # Optional ID and name fields
        with st.expander("Optional: ID and name", expanded=False):
            col_id, col_name = st.columns(2)
            with col_id:
                carrier_id = st.text_input(
                    "Carrier ID",
                    placeholder="(auto)",
                    help="Unique identifier - leave empty for auto-generation",
                )
            with col_name:
                carrier_name = st.text_input(
                    "Name",
                    placeholder="(auto)",
                    help="Descriptive name - leave empty for auto-generation",
                )

        # Option to save permanently
        save_to_file = st.checkbox(
            "Save permanently",
            value=False,
            help="Save carrier to file - will be available in future sessions",
        )

        submitted = st.form_submit_button("Add carrier", type="primary")

        if submitted:
            from src.core.carriers import CarrierService
            from src.core.types import CarrierConfig

            # Auto-generate ID and name if empty
            existing_ids = [c["carrier_id"] for c in st.session_state.custom_carriers]

            if not carrier_id:
                # Generate unique ID based on dimensions
                base_id = f"CARRIER_{width_mm}x{length_mm}x{height_mm}"
                carrier_id = base_id
                counter = 1
                while carrier_id in existing_ids:
                    carrier_id = f"{base_id}_{counter}"
                    counter += 1

            if not carrier_name:
                carrier_name = f"Carrier {width_mm}x{length_mm}x{height_mm}mm"

            # Check if ID already exists (if manually provided)
            if carrier_id in existing_ids:
                st.error(f"Carrier with ID '{carrier_id}' already exists")
            else:
                new_carrier = {
                    "carrier_id": carrier_id,
                    "name": carrier_name,
                    "inner_length_mm": float(length_mm),
                    "inner_width_mm": float(width_mm),
                    "inner_height_mm": float(height_mm),
                    "max_weight_kg": float(max_weight),
                    "is_predefined": False,
                    "is_active": True,
                }
                st.session_state.custom_carriers.append(new_carrier)

                # Save to file if requested
                if save_to_file:
                    service = CarrierService()
                    custom_list = [
                        CarrierConfig(**c)
                        for c in st.session_state.custom_carriers
                        if not c.get("is_predefined", False)
                    ]
                    service.save_custom_carriers(custom_list)
                    st.success(f"Added and saved carrier: {carrier_name}")
                else:
                    st.success(f"Added carrier: {carrier_name} (this session only)")
                st.rerun()


def render_carriers_table() -> None:
    """Display table of defined carriers with delete option and activation toggle."""
    carriers = st.session_state.custom_carriers

    if not carriers:
        st.info("No carriers defined. Add carriers below.")
        return

    st.markdown("**Defined carriers:**")

    # Header row
    header_cols = st.columns([1, 3, 3, 2, 1, 1])
    with header_cols[0]:
        st.markdown("**Active**")
    with header_cols[1]:
        st.markdown("**Carrier**")
    with header_cols[2]:
        st.markdown("**Dimensions (L×W×H)**")
    with header_cols[3]:
        st.markdown("**Max weight**")
    with header_cols[4]:
        st.markdown("**Type**")
    with header_cols[5]:
        st.markdown("")

    for i, carrier in enumerate(carriers):
        is_predefined = carrier.get("is_predefined", False)
        is_active = carrier.get("is_active", True)
        cols = st.columns([1, 3, 3, 2, 1, 1])

        with cols[0]:
            # Checkbox for activation/deactivation
            new_active = st.checkbox(
                "Active",
                value=is_active,
                key=f"carrier_active_{i}",
                label_visibility="collapsed",
                help="Include this carrier in analysis",
            )
            if new_active != is_active:
                st.session_state.custom_carriers[i]["is_active"] = new_active
                st.rerun()

        with cols[1]:
            st.text(f"{carrier['carrier_id']}")
            st.caption(carrier["name"])
        with cols[2]:
            dims = f"{int(carrier['inner_length_mm'])}×{int(carrier['inner_width_mm'])}×{int(carrier['inner_height_mm'])} mm"
            st.text(dims)
        with cols[3]:
            st.text(f"{carrier['max_weight_kg']:.1f} kg")
        with cols[4]:
            if is_predefined:
                st.markdown(":blue[Predef.]")
            else:
                st.markdown(":green[Custom]")
        with cols[5]:
            if is_predefined:
                # Cannot delete predefined carriers
                st.button(
                    "🔒", key=f"lock_carrier_{i}", disabled=True, help="Predefined"
                )
            else:
                # Can delete custom carriers
                if st.button(
                    "✕", key=f"del_carrier_{i}", help=f"Delete {carrier['name']}"
                ):
                    st.session_state.custom_carriers.pop(i)
                    st.rerun()


def render_analysis_tab() -> None:
    """Analysis tab."""
    from src.core.types import CarrierConfig

    st.header("Capacity and performance analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Capacity analysis")

        if st.session_state.masterdata_df is None:
            st.info("Import Masterdata")
        else:
            # Display carriers table
            render_carriers_table()

            # Save all custom carriers button
            custom_count = sum(
                1
                for c in st.session_state.custom_carriers
                if not c.get("is_predefined", False)
            )
            if custom_count > 0:
                if st.button(
                    f"Save {custom_count} custom carrier(s) permanently",
                    help="Save all custom carriers to config file",
                ):
                    from src.core.carriers import CarrierService

                    service = CarrierService()
                    custom_list = [
                        CarrierConfig(**c)
                        for c in st.session_state.custom_carriers
                        if not c.get("is_predefined", False)
                    ]
                    service.save_custom_carriers(custom_list)
                    st.success(f"Saved {len(custom_list)} carrier(s)")

            st.markdown("---")

            # Carrier addition form
            with st.expander("Add carrier", expanded=len(st.session_state.custom_carriers) == 0):
                render_carrier_form()

            # Analysis button
            carriers_defined = len(st.session_state.custom_carriers) > 0

            if not carriers_defined:
                st.warning("Add at least one carrier for analysis")

            # Analysis mode selection
            st.markdown("---")
            analysis_mode = st.radio(
                "Analysis mode",
                options=["Independent (all carriers)", "Prioritized (smallest first)"],
                index=0,
                key="capacity_analysis_mode",
                help="Independent: SKU tested vs all active carriers separately. "
                     "Prioritized: SKU assigned to smallest fitting carrier (by volume).",
                horizontal=True,
            )
            prioritization_mode = analysis_mode == "Prioritized (smallest first)"

            if prioritization_mode:
                st.info(
                    "Prioritized mode: Each SKU will be assigned to the smallest carrier "
                    "it fits into. Carriers are sorted by internal volume (smallest first)."
                )

            # Exclusion settings
            outlier_count = 0
            if st.session_state.quality_result is not None:
                outlier_count = len(st.session_state.quality_result.dq_lists.suspect_outliers)

            with st.expander(
                f"Exclusion settings ({outlier_count} outliers)" if outlier_count > 0 else "Exclusion settings",
                expanded=outlier_count > 0,
            ):
                if outlier_count > 0:
                    st.warning(f"{outlier_count} SKU detected as outliers (values outside normal range)")

                st.checkbox(
                    f"Exclude outliers ({outlier_count} SKU)",
                    value=outlier_count > 0,  # Default: enabled only when outliers exist
                    key="exclude_outliers_checkbox",
                    disabled=outlier_count == 0,
                    help="SKU with suspicious values (dimensions/weight outside normal range)",
                )

                if outlier_count == 0:
                    st.caption("No outliers detected - all SKU will be included in analysis")
                else:
                    st.caption("Borderline filters will be available after running analysis")

            if st.button("Run capacity analysis", disabled=not carriers_defined):
                with st.spinner("Analysis in progress..."):
                    try:
                        from src.analytics import CapacityAnalyzer

                        # Convert dictionaries to CarrierConfig
                        carriers = [
                            CarrierConfig(**c)
                            for c in st.session_state.custom_carriers
                        ]

                        # Use borderline threshold from session state
                        borderline_threshold = st.session_state.get("borderline_threshold", 2.0)

                        # Filter out only Outliers from analysis (borderline handled per carrier in UI)
                        df_to_analyze = st.session_state.masterdata_df
                        excluded_outliers_count = 0

                        if st.session_state.quality_result is not None:
                            dq = st.session_state.quality_result.dq_lists

                            # Exclude outliers if checkbox is checked
                            if st.session_state.get("exclude_outliers_checkbox", True):
                                outlier_skus = {item.sku for item in dq.suspect_outliers}
                                if outlier_skus:
                                    excluded_outliers_count = len(outlier_skus)
                                    df_to_analyze = df_to_analyze.filter(
                                        ~pl.col("sku").is_in(list(outlier_skus))
                                    )

                        analyzer = CapacityAnalyzer(
                            carriers=carriers,
                            borderline_threshold_mm=borderline_threshold,
                        )
                        result = analyzer.analyze_dataframe(
                            df_to_analyze,
                            prioritization_mode=prioritization_mode,
                        )
                        st.session_state.capacity_result = result
                        st.session_state.capacity_excluded_outliers = excluded_outliers_count
                        st.session_state.capacity_prioritization_mode = prioritization_mode

                        st.success("Capacity analysis complete")

                    except Exception as e:
                        st.error(f"Error: {e}")

            # Display capacity analysis results
            if st.session_state.capacity_result is not None:
                result = st.session_state.capacity_result
                is_prioritized = st.session_state.get("capacity_prioritization_mode", False)

                st.markdown("---")

                # Show analysis mode info
                if is_prioritized:
                    st.markdown("**Analysis results (Prioritized mode - SKU assigned to smallest fitting carrier):**")
                else:
                    st.markdown("**Analysis results per carrier (Independent mode):**")

                # Show excluded outliers count if any
                excluded_outliers = st.session_state.get("capacity_excluded_outliers", 0)
                if excluded_outliers > 0:
                    st.info(f"Excluded from analysis: {excluded_outliers} outlier SKU")

                # Borderline filters per carrier (only in independent mode)
                if not is_prioritized:
                    with st.expander("Filter borderline SKU", expanded=False):
                        st.caption("Exclude borderline from statistics per carrier:")
                        for carrier_id in result.carriers_analyzed:
                            stats = result.carrier_stats.get(carrier_id)
                            if stats and stats.borderline_count > 0:
                                st.checkbox(
                                    f"{stats.carrier_name}: {stats.borderline_count} borderline SKU",
                                    value=False,
                                    key=f"exclude_borderline_{carrier_id}",
                                )

                # Display results for each carrier separately
                for carrier_id in result.carriers_analyzed:
                    stats = result.carrier_stats.get(carrier_id)
                    if stats:
                        # Special handling for "NONE" in prioritized mode
                        if carrier_id == "NONE":
                            with st.expander(f"Does not fit any carrier", expanded=True):
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric(
                                        "SKU count", stats.not_fit_count,
                                        help="Number of SKU that don't fit any active carrier"
                                    )
                                with col_b:
                                    st.metric(
                                        "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                                        help="Sum of unit volumes for non-fitting SKU"
                                    )
                                with col_c:
                                    st.metric(
                                        "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                                        help="Sum of stock volumes for non-fitting SKU"
                                    )
                            continue

                        # Check if borderline should be excluded for this carrier
                        exclude_borderline = st.session_state.get(
                            f"exclude_borderline_{carrier_id}", False
                        )

                        # Calculate display values based on filter
                        if exclude_borderline and not is_prioritized:
                            display_fit = stats.fit_count
                            display_borderline = 0
                            display_total = stats.fit_count + stats.not_fit_count
                            display_fit_pct = (
                                (stats.fit_count / display_total * 100)
                                if display_total > 0
                                else 0
                            )
                            borderline_help = "EXCLUDED from statistics"
                        else:
                            display_fit = stats.fit_count
                            display_borderline = stats.borderline_count
                            display_fit_pct = stats.fit_percentage
                            borderline_help = "SKU fitting but with margin < threshold (risk of fitting issues)"

                        # In prioritized mode, show "Assigned SKU" instead of FIT/NOT_FIT
                        if is_prioritized:
                            assigned_count = stats.fit_count + stats.borderline_count
                            with st.expander(f"{stats.carrier_name} ({carrier_id})", expanded=True):
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric(
                                        "Assigned SKU", assigned_count,
                                        help="Number of SKU assigned to this carrier (smallest fitting)"
                                    )
                                    if stats.borderline_count > 0:
                                        st.caption(f"({stats.borderline_count} borderline)")
                                with col_b:
                                    st.metric(
                                        "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                                        help="Sum of unit volumes (L×W×H) for assigned SKU"
                                    )
                                with col_c:
                                    st.metric(
                                        "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                                        help="Sum of (unit volume × stock quantity) for assigned SKU"
                                    )
                        else:
                            with st.expander(f"{stats.carrier_name} ({carrier_id})", expanded=True):
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric(
                                        "FIT", display_fit,
                                        help="SKU fitting completely with margin > threshold"
                                    )
                                    st.metric(
                                        "BORDERLINE",
                                        display_borderline if not exclude_borderline else f"({stats.borderline_count})",
                                        help=borderline_help,
                                    )
                                with col_b:
                                    st.metric(
                                        "NOT FIT", stats.not_fit_count,
                                        help="SKU not fitting in this carrier (size or weight exceeded)"
                                    )
                                    st.metric(
                                        "Fit %", f"{display_fit_pct:.1f}%",
                                        help="Percentage of SKU fitting (FIT + BORDERLINE) / Total"
                                        if not exclude_borderline
                                        else "Percentage of SKU fitting (FIT only) / Total (excl. borderline)"
                                    )
                                with col_c:
                                    st.metric(
                                        "Volume (m³)", f"{stats.total_volume_m3:.2f}",
                                        help="Sum of unit volumes (L×W×H) for all fitting SKU"
                                    )
                                    st.metric(
                                        "Stock volume (m³)", f"{stats.stock_volume_m3:.2f}",
                                        help="Sum of (unit volume × stock quantity) for all fitting SKU"
                                    )

    with col2:
        st.subheader("Performance analysis")

        if st.session_state.orders_df is None:
            st.info("Import Orders")
        else:
            # Shift configuration
            st.markdown("**Shift configuration:**")
            shift_config = st.selectbox(
                "Shift schedule",
                options=["Default (2 shifts, Mon-Fri)", "Custom schedule", "From YAML file", "None"],
                index=0,
                help="Select shift schedule for performance analysis",
            )

            shift_schedule = None

            # Custom schedule option
            if shift_config == "Custom schedule":
                st.markdown("**Enter schedule parameters:**")
                col_days, col_hours, col_shifts = st.columns(3)
                with col_days:
                    custom_days = st.number_input(
                        "Days per week",
                        min_value=1,
                        max_value=7,
                        value=5,
                        step=1,
                        help="How many days per week the warehouse operates",
                    )
                with col_hours:
                    custom_hours = st.number_input(
                        "Hours per day",
                        min_value=1,
                        max_value=24,
                        value=8,
                        step=1,
                        help="How many hours per day of work",
                    )
                with col_shifts:
                    custom_shifts = st.number_input(
                        "Shifts per day",
                        min_value=1,
                        max_value=4,
                        value=2,
                        step=1,
                        help="How many shifts per day",
                    )

                # Calculate hours per shift
                hours_per_shift = custom_hours / custom_shifts
                st.info(f"Hours per shift: {hours_per_shift:.1f}h | Total shifts/week: {custom_days * custom_shifts}")

            if shift_config == "From YAML file":
                shifts_file = st.file_uploader(
                    "Schedule file (YAML)",
                    type=["yml", "yaml"],
                    key="shifts_upload",
                )
                if shifts_file is not None:
                    import tempfile
                    from src.analytics import load_shifts

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmp:
                        tmp.write(shifts_file.read())
                        tmp_path = tmp.name

                    try:
                        shift_schedule = load_shifts(tmp_path)
                        st.success("Schedule loaded")
                    except Exception as e:
                        st.error(f"Schedule loading error: {e}")

            if st.button("Run performance analysis"):
                with st.spinner("Analysis in progress..."):
                    try:
                        from src.analytics import PerformanceAnalyzer
                        from src.analytics.shifts import ShiftSchedule
                        from src.core.types import ShiftConfig, WeeklySchedule

                        # Get productive hours from session state
                        productive_hours = st.session_state.get("productive_hours", 7.0)

                        # Create shift schedule
                        if shift_config == "Custom schedule":
                            # Generate shifts based on entered parameters
                            hours_per_shift = custom_hours / custom_shifts
                            productive_hours = min(hours_per_shift - 1, productive_hours)

                            # Generate shift configurations
                            shift_configs = []
                            start_hour = 6  # Start at 6:00
                            for s in range(custom_shifts):
                                end_hour = start_hour + int(hours_per_shift)
                                shift_configs.append(
                                    ShiftConfig(
                                        name=f"S{s+1}",
                                        start=f"{start_hour:02d}:00",
                                        end=f"{end_hour:02d}:00",
                                    )
                                )
                                start_hour = end_hour

                            # Assign shifts to days of the week
                            days_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                            weekly_kwargs = {"productive_hours_per_shift": productive_hours}
                            for i, day in enumerate(days_map):
                                if i < custom_days:
                                    weekly_kwargs[day] = shift_configs
                                else:
                                    weekly_kwargs[day] = []

                            weekly = WeeklySchedule(**weekly_kwargs)
                            shift_schedule = ShiftSchedule(weekly_schedule=weekly)

                        elif shift_config == "Default (2 shifts, Mon-Fri)":
                            weekly = WeeklySchedule(
                                productive_hours_per_shift=productive_hours,
                                mon=[
                                    ShiftConfig(name="S1", start="07:00", end="15:00"),
                                    ShiftConfig(name="S2", start="15:00", end="23:00"),
                                ],
                                tue=[
                                    ShiftConfig(name="S1", start="07:00", end="15:00"),
                                    ShiftConfig(name="S2", start="15:00", end="23:00"),
                                ],
                                wed=[
                                    ShiftConfig(name="S1", start="07:00", end="15:00"),
                                    ShiftConfig(name="S2", start="15:00", end="23:00"),
                                ],
                                thu=[
                                    ShiftConfig(name="S1", start="07:00", end="15:00"),
                                    ShiftConfig(name="S2", start="15:00", end="23:00"),
                                ],
                                fri=[
                                    ShiftConfig(name="S1", start="07:00", end="15:00"),
                                    ShiftConfig(name="S2", start="15:00", end="23:00"),
                                ],
                                sat=[],
                                sun=[],
                            )
                            shift_schedule = ShiftSchedule(weekly_schedule=weekly)

                        analyzer = PerformanceAnalyzer(
                            shift_schedule=shift_schedule,
                            productive_hours_per_shift=productive_hours,
                        )
                        result = analyzer.analyze(st.session_state.orders_df)
                        st.session_state.performance_result = result
                        st.session_state.analysis_complete = True

                        st.success("Performance analysis complete")

                        kpi = result.kpi
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Lines/h (avg)", f"{kpi.avg_lines_per_hour:.1f}")
                            st.metric("Orders/h (avg)", f"{kpi.avg_orders_per_hour:.1f}")
                        with col_b:
                            st.metric("Peak lines/h", kpi.peak_lines_per_hour)
                            st.metric("P95 lines/h", f"{kpi.p95_lines_per_hour:.1f}")

                    except Exception as e:
                        st.error(f"Error: {e}")


def generate_individual_report(report_type: str) -> tuple[str, bytes]:
    """Generate individual report and return (name, data).

    Args:
        report_type: Type of report to generate

    Returns:
        Tuple (filename, csv_data)
    """
    import tempfile
    from src.reporting.csv_writer import CSVWriter
    from src.reporting.main_report import MainReportGenerator
    from src.reporting.dq_reports import DQReportGenerator

    writer = CSVWriter()

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)

        if report_type == "Report_Main":
            generator = MainReportGenerator()
            file_path = generator.generate(
                output_dir / "Report_Main.csv",
                quality_result=st.session_state.quality_result,
                capacity_result=st.session_state.capacity_result,
                performance_result=st.session_state.performance_result,
                client_name=st.session_state.client_name or "Client",
            )

        elif report_type == "DQ_Summary":
            generator = DQReportGenerator()
            file_path = generator.generate_summary(
                output_dir / "DQ_Summary.csv",
                st.session_state.quality_result.metrics_after,
            )

        elif report_type == "DQ_MissingCritical":
            generator = DQReportGenerator()
            file_path = generator.generate_missing_critical(
                output_dir / "DQ_MissingCritical.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_SuspectOutliers":
            generator = DQReportGenerator()
            file_path = generator.generate_suspect_outliers(
                output_dir / "DQ_SuspectOutliers.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_HighRiskBorderline":
            generator = DQReportGenerator()
            file_path = generator.generate_high_risk_borderline(
                output_dir / "DQ_HighRiskBorderline.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_Duplicates":
            generator = DQReportGenerator()
            file_path = generator.generate_duplicates(
                output_dir / "DQ_Masterdata_Duplicates.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_Conflicts":
            generator = DQReportGenerator()
            file_path = generator.generate_conflicts(
                output_dir / "DQ_Masterdata_Conflicts.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "Capacity_Results":
            if st.session_state.capacity_result:
                file_path = output_dir / "Capacity_Results.csv"
                writer.write(st.session_state.capacity_result.df, file_path)
            else:
                return None, None

        else:
            return None, None

        with open(file_path, "rb") as f:
            data = f.read()

        return file_path.name, data


def render_reports_tab() -> None:
    """Reports tab."""
    st.header("Report generation")

    # Check available data
    has_quality = st.session_state.quality_result is not None
    has_capacity = st.session_state.capacity_result is not None
    has_performance = st.session_state.performance_result is not None

    if not (has_quality or has_capacity or has_performance):
        st.info("First run validation or analysis in the appropriate tabs")
        return

    # List of reports
    st.subheader("Available reports")

    reports = []

    # Main report - always available if there's any data
    reports.append({
        "name": "Report_Main",
        "description": "Main summary report",
        "available": True,
        "category": "Summary",
    })

    # DQ reports - available if quality_result exists
    if has_quality:
        dq_reports = [
            ("DQ_Summary", "Data quality summary"),
            ("DQ_MissingCritical", "List of SKUs with missing critical data"),
            ("DQ_SuspectOutliers", "List of SKUs with suspect values (outliers)"),
            ("DQ_HighRiskBorderline", "List of SKUs with dimensions near limits"),
            ("DQ_Duplicates", "List of duplicate SKUs"),
            ("DQ_Conflicts", "List of SKUs with value conflicts"),
        ]
        for name, desc in dq_reports:
            reports.append({
                "name": name,
                "description": desc,
                "available": True,
                "category": "Data Quality",
            })

    # Capacity report - available if capacity_result exists
    if has_capacity:
        reports.append({
            "name": "Capacity_Results",
            "description": "Capacity analysis results (SKU fit to carriers)",
            "available": True,
            "category": "Capacity",
        })

    # Display list of reports with download buttons
    for category in ["Summary", "Data Quality", "Capacity"]:
        category_reports = [r for r in reports if r["category"] == category]
        if category_reports:
            st.markdown(f"**{category}:**")

            for report in category_reports:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"- **{report['name']}**: {report['description']}")

                with col2:
                    if report["available"]:
                        if st.button("Download", key=f"download_{report['name']}"):
                            try:
                                filename, data = generate_individual_report(report["name"])
                                if data:
                                    st.download_button(
                                        label=f"Save {filename}",
                                        data=data,
                                        file_name=filename,
                                        mime="text/csv",
                                        key=f"save_{report['name']}",
                                    )
                            except Exception as e:
                                st.error(f"Error: {e}")

    st.markdown("---")

    # Button to download all reports as ZIP
    st.subheader("Download all reports")

    if st.button("Generate ZIP reports", type="primary"):
        with st.spinner("Generating reports..."):
            try:
                import tempfile
                from src.reporting import export_reports

                with tempfile.TemporaryDirectory() as tmp_dir:
                    output_dir = Path(tmp_dir)

                    zip_path = export_reports(
                        output_dir,
                        client_name=st.session_state.client_name or "Client",
                        quality_result=st.session_state.quality_result,
                        capacity_result=st.session_state.capacity_result,
                        performance_result=st.session_state.performance_result,
                    )

                    # Prepare for download
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()

                    st.download_button(
                        label="Download reports (ZIP)",
                        data=zip_data,
                        file_name=zip_path.name,
                        mime="application/zip",
                    )

                    st.success("Reports generated!")

            except Exception as e:
                st.error(f"Generation error: {e}")

    # Main report preview
    st.markdown("---")
    st.subheader("Data preview")

    if has_quality:
        with st.expander("Data Quality", expanded=False):
            qr = st.session_state.quality_result
            st.write(f"- **Quality Score:** {qr.quality_score:.1f}%")
            st.write(f"- **Records:** {qr.total_records}")
            st.write(f"- **Valid:** {qr.valid_records}")
            st.write(f"- **Imputed:** {qr.imputed_records}")

            st.markdown("**Data coverage after imputation:**")
            st.write(f"- Dimensions: {qr.metrics_after.dimensions_coverage_pct:.1f}%")
            st.write(f"- Weight: {qr.metrics_after.weight_coverage_pct:.1f}%")

    if has_capacity:
        with st.expander("Capacity Analysis", expanded=False):
            cr = st.session_state.capacity_result
            st.write(f"- **Total SKU:** {cr.total_sku}")
            st.write(f"- **Carriers:** {', '.join(cr.carriers_analyzed)}")

            st.markdown("**Results per carrier:**")
            for carrier_id in cr.carriers_analyzed:
                stats = cr.carrier_stats.get(carrier_id)
                if stats:
                    st.markdown(f"**{stats.carrier_name}:**")
                    st.write(f"  - FIT: {stats.fit_count} | BORDERLINE: {stats.borderline_count} | NOT_FIT: {stats.not_fit_count}")
                    st.write(f"  - Fit %: {stats.fit_percentage:.1f}% | Volume: {stats.total_volume_m3:.2f} m³")

    if has_performance:
        with st.expander("Performance Analysis", expanded=False):
            pr = st.session_state.performance_result
            kpi = pr.kpi
            st.write(f"- **Lines:** {kpi.total_lines}")
            st.write(f"- **Orders:** {kpi.total_orders}")
            st.write(f"- **Units:** {kpi.total_units}")
            st.write(f"- **Avg lines/h:** {kpi.avg_lines_per_hour:.1f}")
            st.write(f"- **Peak lines/h:** {kpi.peak_lines_per_hour}")
            st.write(f"- **P95 lines/h:** {kpi.p95_lines_per_hour:.1f}")


def main() -> None:
    """Main application function."""
    init_session_state()
    render_sidebar()
    render_tabs()


if __name__ == "__main__":
    main()
