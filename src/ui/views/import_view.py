"""Import view - data import tab with column mapping UI."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from src.ui.layout import (
    render_section_header,
    render_status_badge,
    render_success_box,
    render_error_box,
    render_info_box,
    render_spacer,
)
from src.ui.theme import COLORS

if TYPE_CHECKING:
    from src.ingest import MappingResult


def _get_field_status_html(is_mapped: bool) -> str:
    """Return HTML for field status indicator with colored background (dark theme).

    Args:
        is_mapped: Whether this field has a column mapped to it

    Returns:
        HTML string for the status indicator
    """
    if is_mapped:
        # Green - field is mapped (dark theme)
        return f"""<div style="background-color: rgba(76, 175, 80, 0.15); padding: 6px 10px;
                  border-radius: 4px; border-left: 4px solid {COLORS["primary"]}; margin-bottom: 4px;">
                  <small style="color: {COLORS["primary"]}; font-weight: 500;">✓ Done</small></div>"""
    else:
        # Red - field is not mapped (dark theme)
        return f"""<div style="background-color: rgba(244, 67, 54, 0.15); padding: 6px 10px;
                  border-radius: 4px; border-left: 4px solid {COLORS["error"]}; margin-bottom: 4px;">
                  <small style="color: {COLORS["error"]}; font-weight: 500;">⚠ Missing</small></div>"""


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
    render_section_header("Column mapping", "🔗")

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


def render_mapping_status(mapping_result: "MappingResult") -> bool:
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
                dup_fields.append(f"{field_name} ← {col_mapping.source_column}")
        # Styled error box for duplicates
        dup_list = " • ".join(dup_fields)
        render_error_box(f"Duplicate column mappings: {dup_list}")
        has_errors = True

    # Mapping summary with styled content
    with st.expander("📋 Mapping summary", expanded=False):
        for field_name, col_mapping in mapping_result.mappings.items():
            source = col_mapping.source_column
            badge_color = COLORS["primary"] if col_mapping.is_auto else COLORS["info"]
            badge_text = "auto" if col_mapping.is_auto else "manual"
            st.markdown(
                f'<div style="padding: 4px 0; color: {COLORS["text"]};">'
                f'<strong>{field_name}</strong> ← <code style="background: {COLORS["surface_light"]}; '
                f'padding: 2px 6px; border-radius: 4px;">{source}</code> '
                f'<span style="color: {badge_color}; font-size: 0.8rem;">({badge_text})</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Unmapped columns in separate expander for cleaner display
    if mapping_result.unmapped_columns:
        count = len(mapping_result.unmapped_columns)
        with st.expander(f"ℹ️ {count} unmapped columns from file"):
            cols_text = ", ".join(mapping_result.unmapped_columns)
            st.markdown(
                f'<p style="color: {COLORS["text_secondary"]}; font-size: 0.9rem;">{cols_text}</p>',
                unsafe_allow_html=True,
            )

    return has_errors


def render_masterdata_import() -> None:
    """Import Masterdata with mapping step."""
    from src.ingest import (
        FileReader,
        MASTERDATA_SCHEMA,
        create_masterdata_wizard,
        MasterdataIngestPipeline,
    )
    from src.ingest.units import WeightUnit

    history_service = st.session_state.mapping_history_service

    render_section_header("Masterdata", "📦")

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
            reader = FileReader(st.session_state.masterdata_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), use_container_width=True)

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
            # Status badge with count
            render_status_badge(f"✓ {len(st.session_state.masterdata_df)} SKU imported", "success")
            render_spacer(10)

            with st.expander("Data preview", expanded=False):
                st.dataframe(
                    st.session_state.masterdata_df.head(20).to_pandas(),
                    use_container_width=True,
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
    from src.ingest import (
        FileReader,
        ORDERS_SCHEMA,
        create_orders_wizard,
        OrdersIngestPipeline,
    )

    history_service = st.session_state.mapping_history_service

    render_section_header("Orders", "📋")

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
            st.dataframe(preview_df.to_pandas(), use_container_width=True)

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
            # Status badge with count
            render_status_badge(f"✓ {len(st.session_state.orders_df)} lines imported", "success")
            render_spacer(10)

            with st.expander("Data preview", expanded=False):
                st.dataframe(
                    st.session_state.orders_df.head(20).to_pandas(),
                    use_container_width=True,
                )

        if st.button("Import new file", key="orders_new_import"):
            st.session_state.orders_mapping_step = "upload"
            st.session_state.orders_file_columns = None
            st.session_state.orders_mapping_result = None
            st.session_state.orders_temp_path = None
            st.session_state.orders_df = None
            st.rerun()


def render_import_view() -> None:
    """Render the Import tab content."""
    st.markdown(
        f'<h2 style="color: {COLORS["text"]}; margin-bottom: 1.5rem;">📁 Data Import</h2>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        render_masterdata_import()

    with col2:
        render_orders_import()
