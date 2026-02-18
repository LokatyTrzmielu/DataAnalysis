"""Import view - data import tab with column mapping UI."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from src.ui.layout import (
    render_error_box,
    render_forward_guidance,
    render_section_header,
    render_spacer,
    render_status_button,
)

if TYPE_CHECKING:
    from src.ingest import MappingResult



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


def render_mapping_ui(
    file_columns: list[str],
    mapping_result: "MappingResult",
    schema: dict,
    key_prefix: str = "md",
    required_left_fields: list[str] | None = None,
    optional_inline: bool = False,
) -> "MappingResult":
    """Render column mapping UI with configurable layout.

    Args:
        file_columns: Columns from loaded file
        mapping_result: Auto-mapping result
        schema: MASTERDATA_SCHEMA or ORDERS_SCHEMA
        key_prefix: Prefix for widget keys
        required_left_fields: If set, splits required fields into left/right columns
        optional_inline: If True, renders optional fields in a right column beside required

    Returns:
        Updated MappingResult with user selections
    """
    render_section_header("Column mapping", "🔗")

    required_fields = [f for f, cfg in schema.items() if cfg["required"]]
    optional_fields = [f for f, cfg in schema.items() if not cfg["required"]]
    dropdown_options = ["-- Don't map --"] + list(file_columns)
    user_mappings = {}

    def render_field(field_name: str) -> None:
        field_cfg = schema[field_name]
        widget_key = f"{key_prefix}_map_{field_name}"

        current_mapping = mapping_result.mappings.get(field_name)
        current_value = current_mapping.source_column if current_mapping else None

        if current_value and current_value in file_columns:
            default_idx = file_columns.index(current_value) + 1
        else:
            default_idx = 0

        current_selection = st.session_state.get(widget_key)
        is_mapped = current_selection is not None and current_selection != "-- Don't map --"
        if current_selection is None:
            is_mapped = current_value is not None

        marker_class = "fsm-mapped" if is_mapped else "fsm-missing"
        st.markdown(f'<span class="{marker_class}" style="display:none;"></span>', unsafe_allow_html=True)
        selected = st.selectbox(
            field_name,
            options=dropdown_options,
            index=default_idx,
            key=widget_key,
            help=field_cfg["description"],
        )

        if selected != "-- Don't map --":
            user_mappings[field_name] = selected

    if required_left_fields is not None:
        # Branch A: 2-column split for required fields (Masterdata)
        left_fields = [f for f in required_fields if f in required_left_fields]
        right_fields = [f for f in required_fields if f not in required_left_fields]
        col_left, col_right = st.columns([1, 1])
        with col_left:
            for fn in left_fields:
                render_field(fn)
        with col_right:
            for fn in right_fields:
                render_field(fn)
        if optional_fields:
            with st.expander("⏱ Optional fields", expanded=False):
                for fn in optional_fields:
                    render_field(fn)

    elif optional_inline and optional_fields:
        # Branch B: required left | optional right (Orders)
        col_req, col_opt = st.columns([1, 1])
        with col_req:
            for fn in required_fields:
                render_field(fn)
        with col_opt:
            render_section_header("Optional fields", "⏱")
            for fn in optional_fields:
                render_field(fn)

    else:
        # Branch C: original single-column behavior (default)
        for fn in required_fields:
            render_field(fn)
        if optional_fields:
            with st.expander("⏱ Optional fields", expanded=False):
                for fn in optional_fields:
                    render_field(fn)

    return build_mapping_result_from_selections(user_mappings, file_columns, schema, mapping_result)


def render_mapping_status(mapping_result: "MappingResult") -> bool:
    """Display mapping validation errors (duplicates, missing required).

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
                dup_fields.append(f"{field_name} ← {col_mapping.source_column}")
        # Styled error box for duplicates
        dup_list = " • ".join(dup_fields)
        render_error_box(f"Duplicate column mappings: {dup_list}")
        has_errors = True

    return has_errors


def render_masterdata_import() -> None:
    """Import Masterdata — persistent uploader with inline mapping."""
    from src.ingest import (
        FileReader,
        MASTERDATA_SCHEMA,
        create_masterdata_wizard,
        MasterdataIngestPipeline,
    )
    from src.ingest.units import WeightUnit

    history_service = st.session_state.mapping_history_service

    st.header("📁 Masterdata Import")

    # File uploader — always visible
    masterdata_file = st.file_uploader(
        "",
        type=["xlsx", "csv", "txt"],
        key="masterdata_upload",
        label_visibility="collapsed",
    )

    if masterdata_file is not None:
        file_id = f"{masterdata_file.name}_{masterdata_file.size}"
        if st.session_state.get("masterdata_last_file_id") != file_id:
            st.session_state.masterdata_last_file_id = file_id
            with st.spinner("Analyzing file..."):
                try:
                    suffix = Path(masterdata_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(masterdata_file.read())
                        tmp_path = tmp.name

                    reader = FileReader(tmp_path)
                    columns = reader.get_columns()

                    wizard = create_masterdata_wizard(history_service)
                    client_name = st.session_state.get("client_name", "")
                    auto_mapping = wizard.auto_map(columns, client_name)

                    st.session_state.masterdata_temp_path = tmp_path
                    st.session_state.masterdata_file_columns = columns
                    st.session_state.masterdata_mapping_result = auto_mapping
                    st.session_state.masterdata_original_mapping = auto_mapping
                    # Reset downstream data for new file
                    st.session_state.masterdata_df = None
                    st.session_state.quality_result = None
                    st.session_state.capacity_result = None
                    st.rerun()

                except Exception as e:
                    st.error(f"File analysis error: {e}")

    # Show mapping UI when a file has been analyzed
    if st.session_state.get("masterdata_file_columns") is not None:
        columns = st.session_state.masterdata_file_columns
        mapping = st.session_state.masterdata_mapping_result

        # Data preview
        st.markdown('<div class="data-preview-container">', unsafe_allow_html=True)
        with st.expander("👁️ Data preview", expanded=True):
            reader = FileReader(st.session_state.masterdata_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        render_spacer(8)

        # Mapping UI
        updated_mapping = render_mapping_ui(
            file_columns=columns,
            mapping_result=mapping,
            schema=MASTERDATA_SCHEMA,
            key_prefix="md",
            required_left_fields=["sku", "weight", "stock"],
        )

        # Save updated mapping
        st.session_state.masterdata_mapping_result = updated_mapping

        # Validation errors
        has_mapping_errors = render_mapping_status(updated_mapping)

        render_spacer(12)

        # Weight unit selection
        weight_col, _ = st.columns([2, 3])
        with weight_col:
            weight_unit_option = st.selectbox(
                "Weight unit in source file",
                options=["Auto-detect", "Grams (g)", "Kilograms (kg)"],
                index=0,
                key="md_weight_unit",
                help="Select unit if auto-detection fails for light items",
            )

        # Import button on the left
        btn_col_import, _ = st.columns([1, 4])
        with btn_col_import:
            import_disabled = not updated_mapping.is_complete or has_mapping_errors
            if st.button(
                "Import Masterdata",
                key="md_do_import",
                disabled=import_disabled,
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Importing..."):
                    try:
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
                        # Reset Capacity pipeline statuses
                        st.session_state.quality_result = None
                        st.session_state.capacity_result = None

                        # Record user corrections to history
                        original = st.session_state.masterdata_original_mapping
                        if original is not None and history_service is not None:
                            wizard = create_masterdata_wizard(history_service)
                            client_name = st.session_state.get("client_name", "")
                            wizard.record_user_corrections(
                                original, updated_mapping, client_name
                            )
                            history_service.save_history()

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        # Auto-navigate to Validation tab
                        st.session_state.capacity_subtab = "Validation"
                        st.rerun()

                    except Exception as e:
                        st.error(f"Import error: {e}")


def render_orders_import() -> None:
    """Import Orders — persistent uploader with inline mapping."""
    from src.ingest import (
        FileReader,
        ORDERS_SCHEMA,
        create_orders_wizard,
        OrdersIngestPipeline,
    )

    history_service = st.session_state.mapping_history_service

    st.header("📝 Orders Import")

    # File uploader — always visible
    orders_file = st.file_uploader(
        "",
        type=["xlsx", "csv", "txt"],
        key="orders_upload",
        label_visibility="collapsed",
    )

    if orders_file is not None:
        file_id = f"{orders_file.name}_{orders_file.size}"
        if st.session_state.get("orders_last_file_id") != file_id:
            st.session_state.orders_last_file_id = file_id
            with st.spinner("Analyzing file..."):
                try:
                    suffix = Path(orders_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(orders_file.read())
                        tmp_path = tmp.name

                    reader = FileReader(tmp_path)
                    columns = reader.get_columns()

                    wizard = create_orders_wizard(history_service)
                    client_name = st.session_state.get("client_name", "")
                    auto_mapping = wizard.auto_map(columns, client_name)

                    st.session_state.orders_temp_path = tmp_path
                    st.session_state.orders_file_columns = columns
                    st.session_state.orders_mapping_result = auto_mapping
                    st.session_state.orders_original_mapping = auto_mapping
                    # Reset downstream data for new file
                    st.session_state.orders_df = None
                    st.session_state.performance_result = None
                    st.rerun()

                except Exception as e:
                    st.error(f"File analysis error: {e}")

    # Show mapping UI when a file has been analyzed
    if st.session_state.get("orders_file_columns") is not None:
        columns = st.session_state.orders_file_columns
        mapping = st.session_state.orders_mapping_result

        # Data preview
        st.markdown('<div class="data-preview-container">', unsafe_allow_html=True)
        with st.expander("👁️ Data preview", expanded=True):
            reader = FileReader(st.session_state.orders_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        render_spacer(8)

        # Mapping UI
        updated_mapping = render_mapping_ui(
            file_columns=columns,
            mapping_result=mapping,
            schema=ORDERS_SCHEMA,
            key_prefix="orders",
            optional_inline=True,
        )

        # Save updated mapping
        st.session_state.orders_mapping_result = updated_mapping

        # Validation errors
        has_mapping_errors = render_mapping_status(updated_mapping)

        render_spacer(12)

        # Import button on the left
        btn_col_import, _ = st.columns([1, 4])
        with btn_col_import:
            import_disabled = not updated_mapping.is_complete or has_mapping_errors
            if st.button(
                "Import Orders",
                key="orders_do_import",
                disabled=import_disabled,
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Importing..."):
                    try:
                        pipeline = OrdersIngestPipeline()
                        result = pipeline.run(
                            st.session_state.orders_temp_path,
                            mapping=updated_mapping,
                        )

                        st.session_state.orders_df = result.df
                        # Reset Performance pipeline status
                        st.session_state.performance_result = None

                        # Record user corrections to history
                        original = st.session_state.orders_original_mapping
                        if original is not None and history_service is not None:
                            wizard = create_orders_wizard(history_service)
                            client_name = st.session_state.get("client_name", "")
                            wizard.record_user_corrections(
                                original, updated_mapping, client_name
                            )
                            history_service.save_history()

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        # Auto-navigate to Validation tab
                        st.session_state.performance_subtab = "Validation"
                        st.rerun()

                    except Exception as e:
                        st.error(f"Import error: {e}")


def render_import_view() -> None:
    """Render the Import tab content."""
    st.header("Data Import")

    col1, col2 = st.columns(2)

    with col1:
        render_masterdata_import()

    with col2:
        render_orders_import()
