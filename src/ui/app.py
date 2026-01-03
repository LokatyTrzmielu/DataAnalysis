"""Glowna aplikacja Streamlit DataAnalysis."""

import sys
from pathlib import Path

# Dodaj katalog glowny projektu do PYTHONPATH
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

# Konfiguracja strony
st.set_page_config(
    page_title="DataAnalysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Inicjalizacja session state."""
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
        "masterdata_temp_path": None,
        "masterdata_mapping_step": "upload",
        # Orders mapping state
        "orders_file_columns": None,
        "orders_mapping_result": None,
        "orders_temp_path": None,
        "orders_mapping_step": "upload",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    """Renderuj sidebar z parametrami."""
    with st.sidebar:
        st.title("DataAnalysis")
        st.markdown("---")

        # Nazwa klienta
        st.session_state.client_name = st.text_input(
            "Nazwa klienta",
            value=st.session_state.client_name,
            placeholder="np. Klient_ABC",
        )

        st.markdown("---")
        st.subheader("Parametry analizy")

        # Utilization
        st.session_state.utilization_vlm = st.slider(
            "Utilization VLM",
            min_value=0.5,
            max_value=1.0,
            value=0.75,
            step=0.05,
            help="Wspolczynnik wykorzystania dla Vertical Lift Module",
        )

        st.session_state.utilization_mib = st.slider(
            "Utilization MiB",
            min_value=0.5,
            max_value=1.0,
            value=0.68,
            step=0.05,
            help="Wspolczynnik wykorzystania dla Mini-load in Box",
        )

        # Productive hours
        st.session_state.productive_hours = st.slider(
            "Godziny produktywne / zmiana",
            min_value=4.0,
            max_value=8.0,
            value=7.0,
            step=0.5,
            help="Efektywny czas pracy na zmiane",
        )

        # Borderline threshold
        st.session_state.borderline_threshold = st.slider(
            "Borderline threshold (mm)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Prog dla oznaczenia SKU jako BORDERLINE (blisko limitu nosnika)",
        )

        st.markdown("---")
        st.subheader("Imputacja")

        st.session_state.imputation_enabled = st.checkbox(
            "Wlacz imputacje",
            value=True,
            help="Uzupelniaj brakujace wartosci mediana",
        )

        st.markdown("---")

        # Status
        if st.session_state.masterdata_df is not None:
            st.success(f"Masterdata: {len(st.session_state.masterdata_df)} SKU")
        if st.session_state.orders_df is not None:
            st.success(f"Orders: {len(st.session_state.orders_df)} linii")
        if st.session_state.analysis_complete:
            st.success("Analiza zakonczona")


def render_tabs() -> None:
    """Renderuj glowne zakladki."""
    tabs = st.tabs(["📁 Import", "✅ Walidacja", "📊 Analiza", "📄 Raporty"])

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
) -> "MappingResult":
    """Buduj MappingResult z wyborow uzytkownika.

    Args:
        user_mappings: Slownik target_field -> source_column
        file_columns: Wszystkie kolumny z pliku
        schema: MASTERDATA_SCHEMA lub ORDERS_SCHEMA

    Returns:
        MappingResult
    """
    from src.ingest import MappingResult, ColumnMapping

    mappings = {}
    used_columns = set()

    for field_name, source_col in user_mappings.items():
        mappings[field_name] = ColumnMapping(
            target_field=field_name,
            source_column=source_col,
            confidence=1.0,
            is_auto=False,
        )
        used_columns.add(source_col)

    # Wyznacz brakujace wymagane pola
    missing_required = []
    for field_name, field_cfg in schema.items():
        if field_cfg["required"] and field_name not in user_mappings:
            missing_required.append(field_name)

    # Niezmapowane kolumny
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
    """Renderuj UI mapowania kolumn.

    Args:
        file_columns: Kolumny z wczytanego pliku
        mapping_result: Wynik auto-mapowania
        schema: MASTERDATA_SCHEMA lub ORDERS_SCHEMA
        key_prefix: Prefiks dla kluczy widgetow

    Returns:
        Zaktualizowany MappingResult z wyborami uzytkownika
    """
    st.subheader("Mapowanie kolumn")

    # Podziel na wymagane i opcjonalne
    required_fields = [f for f, cfg in schema.items() if cfg["required"]]
    optional_fields = [f for f, cfg in schema.items() if not cfg["required"]]

    # Opcje dropdown: brak + kolumny z pliku
    dropdown_options = ["-- Nie mapuj --"] + list(file_columns)

    user_mappings = {}

    # Sekcja wymaganych pol
    st.markdown("**Wymagane pola:**")

    # Uzyj 5 kolumn dla wymaganych pol
    cols = st.columns(len(required_fields))
    for i, field_name in enumerate(required_fields):
        with cols[i]:
            field_cfg = schema[field_name]

            # Pobierz aktualne mapowanie
            current_mapping = mapping_result.mappings.get(field_name)
            current_value = current_mapping.source_column if current_mapping else None

            # Znajdz indeks dla domyslnego wyboru
            if current_value and current_value in file_columns:
                default_idx = file_columns.index(current_value) + 1
            else:
                default_idx = 0

            # Wskaznik confidence
            confidence_indicator = ""
            if current_mapping:
                if current_mapping.confidence >= 0.9:
                    confidence_indicator = " (auto)"
                elif current_mapping.confidence >= 0.5:
                    confidence_indicator = " (~)"

            # Dropdown
            selected = st.selectbox(
                f"{field_name}{confidence_indicator}",
                options=dropdown_options,
                index=default_idx,
                key=f"{key_prefix}_map_{field_name}",
                help=field_cfg["description"],
            )

            if selected != "-- Nie mapuj --":
                user_mappings[field_name] = selected

    # Sekcja opcjonalnych pol
    if optional_fields:
        st.markdown("**Opcjonalne pola:**")

        opt_cols = st.columns(len(optional_fields))
        for i, field_name in enumerate(optional_fields):
            with opt_cols[i]:
                field_cfg = schema[field_name]
                current_mapping = mapping_result.mappings.get(field_name)
                current_value = current_mapping.source_column if current_mapping else None

                if current_value and current_value in file_columns:
                    default_idx = file_columns.index(current_value) + 1
                else:
                    default_idx = 0

                selected = st.selectbox(
                    f"{field_name}",
                    options=dropdown_options,
                    index=default_idx,
                    key=f"{key_prefix}_map_{field_name}",
                    help=field_cfg["description"],
                )

                if selected != "-- Nie mapuj --":
                    user_mappings[field_name] = selected

    # Zbuduj zaktualizowany MappingResult
    return build_mapping_result_from_selections(user_mappings, file_columns, schema)


def render_mapping_status(mapping_result: "MappingResult", schema: dict) -> None:
    """Wyswietl status mapowania i komunikaty walidacji.

    Args:
        mapping_result: Aktualny wynik mapowania
        schema: MASTERDATA_SCHEMA lub ORDERS_SCHEMA
    """
    if mapping_result.is_complete:
        st.success("Wszystkie wymagane pola zmapowane")
    else:
        missing = ", ".join(mapping_result.missing_required)
        st.error(f"Brakuje wymaganych pol: {missing}")

    # Podsumowanie mapowania
    with st.expander("Podsumowanie mapowania", expanded=False):
        for field_name, col_mapping in mapping_result.mappings.items():
            source = col_mapping.source_column
            auto_label = "auto" if col_mapping.is_auto else "manual"
            st.write(f"- **{field_name}** <- `{source}` ({auto_label})")

        if mapping_result.unmapped_columns:
            st.write("**Niezmapowane kolumny:**")
            unmapped_display = mapping_result.unmapped_columns[:10]
            st.write(", ".join(unmapped_display))
            if len(mapping_result.unmapped_columns) > 10:
                st.write(f"... i {len(mapping_result.unmapped_columns) - 10} wiecej")


def render_masterdata_import() -> None:
    """Import Masterdata z krokiem mapowania."""
    import tempfile
    from src.ingest import (
        FileReader,
        MASTERDATA_SCHEMA,
        create_masterdata_wizard,
        MasterdataIngestPipeline,
    )

    st.subheader("Masterdata")

    step = st.session_state.get("masterdata_mapping_step", "upload")

    # Krok 1: Upload pliku
    if step == "upload":
        masterdata_file = st.file_uploader(
            "Wybierz plik Masterdata",
            type=["xlsx", "csv", "txt"],
            key="masterdata_upload",
        )

        if masterdata_file is not None:
            if st.button("Dalej - Mapowanie kolumn", key="md_to_mapping"):
                with st.spinner("Analizowanie pliku..."):
                    try:
                        # Zapisz do pliku tymczasowego
                        suffix = Path(masterdata_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(masterdata_file.read())
                            tmp_path = tmp.name

                        # Wczytaj kolumny i uruchom auto-mapowanie
                        reader = FileReader(tmp_path)
                        columns = reader.get_columns()

                        wizard = create_masterdata_wizard()
                        auto_mapping = wizard.auto_map(columns)

                        # Zapisz w session state
                        st.session_state.masterdata_temp_path = tmp_path
                        st.session_state.masterdata_file_columns = columns
                        st.session_state.masterdata_mapping_result = auto_mapping
                        st.session_state.masterdata_mapping_step = "mapping"
                        st.rerun()

                    except Exception as e:
                        st.error(f"Blad analizy pliku: {e}")

    # Krok 2: Mapowanie kolumn
    elif step == "mapping":
        columns = st.session_state.masterdata_file_columns
        mapping = st.session_state.masterdata_mapping_result

        # Podglad danych
        with st.expander("Podglad danych", expanded=False):
            from src.ingest import FileReader
            reader = FileReader(st.session_state.masterdata_temp_path)
            preview_df = reader.get_preview(n_rows=5)
            st.dataframe(preview_df.to_pandas(), use_container_width=True)

        # UI mapowania
        updated_mapping = render_mapping_ui(
            file_columns=columns,
            mapping_result=mapping,
            schema=MASTERDATA_SCHEMA,
            key_prefix="md",
        )

        # Zapisz zaktualizowane mapowanie
        st.session_state.masterdata_mapping_result = updated_mapping

        # Status
        render_mapping_status(updated_mapping, MASTERDATA_SCHEMA)

        # Przyciski akcji
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button("Wstecz", key="md_back_to_upload"):
                st.session_state.masterdata_mapping_step = "upload"
                st.session_state.masterdata_file_columns = None
                st.session_state.masterdata_mapping_result = None
                st.rerun()

        with btn_col2:
            import_disabled = not updated_mapping.is_complete
            if st.button(
                "Importuj Masterdata",
                key="md_do_import",
                disabled=import_disabled,
                type="primary",
            ):
                with st.spinner("Importowanie..."):
                    try:
                        pipeline = MasterdataIngestPipeline()
                        result = pipeline.run(
                            st.session_state.masterdata_temp_path,
                            mapping=updated_mapping,
                        )

                        st.session_state.masterdata_df = result.df
                        st.session_state.masterdata_mapping_step = "complete"

                        st.success(f"Zaimportowano {result.rows_imported} wierszy")

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        st.rerun()

                    except Exception as e:
                        st.error(f"Blad importu: {e}")

    # Krok 3: Zakonczony import
    elif step == "complete":
        if st.session_state.masterdata_df is not None:
            st.success(f"Masterdata: {len(st.session_state.masterdata_df)} SKU")

            with st.expander("Podglad danych", expanded=False):
                st.dataframe(
                    st.session_state.masterdata_df.head(20).to_pandas(),
                    use_container_width=True
                )

        if st.button("Importuj nowy plik", key="md_new_import"):
            st.session_state.masterdata_mapping_step = "upload"
            st.session_state.masterdata_file_columns = None
            st.session_state.masterdata_mapping_result = None
            st.session_state.masterdata_temp_path = None
            st.session_state.masterdata_df = None
            st.rerun()


def render_import_tab() -> None:
    """Zakladka Import."""
    st.header("Import danych")

    col1, col2 = st.columns(2)

    with col1:
        render_masterdata_import()

    with col2:
        st.subheader("Orders")
        orders_file = st.file_uploader(
            "Wybierz plik Orders",
            type=["xlsx", "csv", "txt"],
            key="orders_upload",
        )

        if orders_file is not None:
            if st.button("Importuj Orders", key="import_orders"):
                with st.spinner("Importowanie..."):
                    try:
                        import tempfile
                        from src.ingest import ingest_orders

                        suffix = Path(orders_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(orders_file.read())
                            tmp_path = tmp.name

                        result = ingest_orders(tmp_path)
                        st.session_state.orders_df = result.df

                        st.success(f"Zaimportowano {result.rows_imported} wierszy")

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        st.dataframe(result.df.head(10).to_pandas(), use_container_width=True)

                    except Exception as e:
                        st.error(f"Blad importu: {e}")


def render_validation_tab() -> None:
    """Zakladka Walidacja."""
    st.header("Walidacja i jakosc danych")

    if st.session_state.masterdata_df is None:
        st.info("Najpierw zaimportuj dane Masterdata w zakladce Import")
        return

    if st.button("Uruchom walidacje", key="run_validation"):
        with st.spinner("Walidacja w toku..."):
            try:
                from src.quality import run_quality_pipeline

                result = run_quality_pipeline(
                    st.session_state.masterdata_df,
                    enable_imputation=st.session_state.get("imputation_enabled", True),
                )
                st.session_state.quality_result = result
                st.session_state.masterdata_df = result.df

                st.success("Walidacja zakonczona")

            except Exception as e:
                st.error(f"Blad walidacji: {e}")

    # Wyswietl wyniki
    if st.session_state.quality_result is not None:
        result = st.session_state.quality_result

        # Metryki
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Quality Score", f"{result.quality_score:.1f}%")
        with col2:
            st.metric("Rekordow", result.total_records)
        with col3:
            st.metric("Poprawnych", result.valid_records)
        with col4:
            st.metric("Imputowanych", result.imputed_records)

        st.markdown("---")

        # Pokrycie
        st.subheader("Pokrycie danych")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Przed imputacja:**")
            st.progress(result.metrics_before.dimensions_coverage_pct / 100,
                       text=f"Wymiary: {result.metrics_before.dimensions_coverage_pct:.1f}%")
            st.progress(result.metrics_before.weight_coverage_pct / 100,
                       text=f"Waga: {result.metrics_before.weight_coverage_pct:.1f}%")

        with col2:
            st.write("**Po imputacji:**")
            st.progress(result.metrics_after.dimensions_coverage_pct / 100,
                       text=f"Wymiary: {result.metrics_after.dimensions_coverage_pct:.1f}%")
            st.progress(result.metrics_after.weight_coverage_pct / 100,
                       text=f"Waga: {result.metrics_after.weight_coverage_pct:.1f}%")

        # Problemy
        st.subheader("Wykryte problemy")
        dq = result.dq_lists
        problems = {
            "Missing Critical": len(dq.missing_critical),
            "Outliers": len(dq.suspect_outliers),
            "Borderline": len(dq.high_risk_borderline),
            "Duplikaty": len(dq.duplicates),
            "Konflikty": len(dq.conflicts),
        }

        for name, count in problems.items():
            if count > 0:
                st.warning(f"{name}: {count}")
            else:
                st.success(f"{name}: 0")


def get_default_carriers() -> list:
    """Pobierz domyslna liste nosnikow."""
    from src.core.types import CarrierConfig

    return [
        CarrierConfig(
            carrier_id="TRAY_S",
            name="Tray Small",
            inner_length_mm=600,
            inner_width_mm=400,
            inner_height_mm=100,
            max_weight_kg=50,
        ),
        CarrierConfig(
            carrier_id="TRAY_M",
            name="Tray Medium",
            inner_length_mm=600,
            inner_width_mm=400,
            inner_height_mm=200,
            max_weight_kg=80,
        ),
        CarrierConfig(
            carrier_id="TRAY_L",
            name="Tray Large",
            inner_length_mm=600,
            inner_width_mm=400,
            inner_height_mm=350,
            max_weight_kg=120,
        ),
        CarrierConfig(
            carrier_id="TRAY_XL",
            name="Tray Extra Large",
            inner_length_mm=800,
            inner_width_mm=600,
            inner_height_mm=400,
            max_weight_kg=150,
        ),
    ]


def render_analysis_tab() -> None:
    """Zakladka Analiza."""
    st.header("Analiza pojemnosciowa i wydajnosciowa")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Analiza pojemnosciowa")

        if st.session_state.masterdata_df is None:
            st.info("Zaimportuj Masterdata")
        else:
            # Wybor nosnikow (multiselect)
            all_carriers = get_default_carriers()
            carrier_options = {c.carrier_id: f"{c.name} ({c.inner_length_mm}x{c.inner_width_mm}x{c.inner_height_mm}mm)" for c in all_carriers}

            selected_carrier_ids = st.multiselect(
                "Wybierz nosniki do analizy",
                options=list(carrier_options.keys()),
                default=["TRAY_M", "TRAY_L"],
                format_func=lambda x: carrier_options[x],
                help="Wybierz nosniki, do ktorych ma byc dopasowane SKU",
            )

            if not selected_carrier_ids:
                st.warning("Wybierz co najmniej jeden nosnik")

            # Szczegoly wybranych nosnikow
            with st.expander("Szczegoly nosnikow", expanded=False):
                for carrier in all_carriers:
                    if carrier.carrier_id in selected_carrier_ids:
                        st.write(f"**{carrier.name}** ({carrier.carrier_id})")
                        st.write(f"  - Wymiary: {carrier.inner_length_mm} x {carrier.inner_width_mm} x {carrier.inner_height_mm} mm")
                        st.write(f"  - Max waga: {carrier.max_weight_kg} kg")

            if st.button("Uruchom analize pojemnosciowa", disabled=not selected_carrier_ids):
                with st.spinner("Analiza w toku..."):
                    try:
                        from src.analytics import CapacityAnalyzer

                        # Filtruj wybrane nosniki
                        selected_carriers = [c for c in all_carriers if c.carrier_id in selected_carrier_ids]

                        # Uzyj borderline threshold z session state
                        borderline_threshold = st.session_state.get("borderline_threshold", 2.0)

                        analyzer = CapacityAnalyzer(
                            carriers=selected_carriers,
                            borderline_threshold_mm=borderline_threshold,
                        )
                        result = analyzer.analyze_dataframe(st.session_state.masterdata_df)
                        st.session_state.capacity_result = result

                        st.success("Analiza pojemnosciowa zakonczona")

                        # Wyniki
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("FIT", result.fit_count)
                            st.metric("BORDERLINE", result.borderline_count)
                        with col_b:
                            st.metric("NOT FIT", result.not_fit_count)
                            st.metric("Fit %", f"{result.fit_percentage:.1f}%")

                    except Exception as e:
                        st.error(f"Blad: {e}")

    with col2:
        st.subheader("Analiza wydajnosciowa")

        if st.session_state.orders_df is None:
            st.info("Zaimportuj Orders")
        else:
            # Konfiguracja zmian
            st.markdown("**Konfiguracja zmian:**")
            shift_config = st.selectbox(
                "Harmonogram zmian",
                options=["Domyslny (2 zmiany, Pn-Pt)", "Z pliku YAML", "Brak"],
                index=0,
                help="Wybierz harmonogram zmian do analizy wydajnosciowej",
            )

            shift_schedule = None
            if shift_config == "Z pliku YAML":
                shifts_file = st.file_uploader(
                    "Plik harmonogramu (YAML)",
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
                        st.success("Harmonogram wczytany")
                    except Exception as e:
                        st.error(f"Blad wczytywania harmonogramu: {e}")

            if st.button("Uruchom analize wydajnosciowa"):
                with st.spinner("Analiza w toku..."):
                    try:
                        from src.analytics import PerformanceAnalyzer
                        from src.analytics.shifts import ShiftSchedule, ShiftScheduleLoader
                        from src.core.types import ShiftConfig, WeeklySchedule

                        # Pobierz productive hours z session state
                        productive_hours = st.session_state.get("productive_hours", 7.0)

                        # Utworz harmonogram zmian
                        if shift_config == "Domyslny (2 zmiany, Pn-Pt)":
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

                        st.success("Analiza wydajnosciowa zakonczona")

                        kpi = result.kpi
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Linii/h (avg)", f"{kpi.avg_lines_per_hour:.1f}")
                            st.metric("Zamowien/h (avg)", f"{kpi.avg_orders_per_hour:.1f}")
                        with col_b:
                            st.metric("Peak linii/h", kpi.peak_lines_per_hour)
                            st.metric("P95 linii/h", f"{kpi.p95_lines_per_hour:.1f}")

                    except Exception as e:
                        st.error(f"Blad: {e}")


def generate_individual_report(report_type: str) -> tuple[str, bytes]:
    """Generuj pojedynczy raport i zwroc (nazwa, dane).

    Args:
        report_type: Typ raportu do wygenerowania

    Returns:
        Tuple (nazwa_pliku, dane_csv)
    """
    import tempfile
    import polars as pl
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
    """Zakladka Raporty."""
    st.header("Generowanie raportow")

    # Sprawdz dostepne dane
    has_quality = st.session_state.quality_result is not None
    has_capacity = st.session_state.capacity_result is not None
    has_performance = st.session_state.performance_result is not None

    if not (has_quality or has_capacity or has_performance):
        st.info("Najpierw przeprowadz walidacje lub analize w odpowiednich zakladkach")
        return

    # Lista raportow
    st.subheader("Dostepne raporty")

    reports = []

    # Raport glowny - zawsze dostepny jesli sa jakies dane
    reports.append({
        "name": "Report_Main",
        "description": "Glowny raport podsumowujacy",
        "available": True,
        "category": "Podsumowanie",
    })

    # Raporty DQ - dostepne jesli jest quality_result
    if has_quality:
        dq_reports = [
            ("DQ_Summary", "Podsumowanie jakosci danych"),
            ("DQ_MissingCritical", "Lista SKU z brakujacymi krytycznymi danymi"),
            ("DQ_SuspectOutliers", "Lista SKU z podejrzanymi wartosciami (outliery)"),
            ("DQ_HighRiskBorderline", "Lista SKU z wymiarami blisko limitow"),
            ("DQ_Duplicates", "Lista zduplikowanych SKU"),
            ("DQ_Conflicts", "Lista SKU z konfliktami wartosci"),
        ]
        for name, desc in dq_reports:
            reports.append({
                "name": name,
                "description": desc,
                "available": True,
                "category": "Data Quality",
            })

    # Raport Capacity - dostepny jesli jest capacity_result
    if has_capacity:
        reports.append({
            "name": "Capacity_Results",
            "description": "Wyniki analizy pojemnosciowej (dopasowanie SKU do nosnikow)",
            "available": True,
            "category": "Capacity",
        })

    # Wyswietl liste raportow z przyciskami pobierania
    for category in ["Podsumowanie", "Data Quality", "Capacity"]:
        category_reports = [r for r in reports if r["category"] == category]
        if category_reports:
            st.markdown(f"**{category}:**")

            for report in category_reports:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"- **{report['name']}**: {report['description']}")

                with col2:
                    if report["available"]:
                        if st.button(f"Pobierz", key=f"download_{report['name']}"):
                            try:
                                filename, data = generate_individual_report(report["name"])
                                if data:
                                    st.download_button(
                                        label=f"Zapisz {filename}",
                                        data=data,
                                        file_name=filename,
                                        mime="text/csv",
                                        key=f"save_{report['name']}",
                                    )
                            except Exception as e:
                                st.error(f"Blad: {e}")

    st.markdown("---")

    # Przycisk do pobrania wszystkich raportow jako ZIP
    st.subheader("Pobierz wszystkie raporty")

    if st.button("Generuj raporty ZIP", type="primary"):
        with st.spinner("Generowanie raportow..."):
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

                    # Przygotuj do pobrania
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()

                    st.download_button(
                        label="Pobierz raporty (ZIP)",
                        data=zip_data,
                        file_name=zip_path.name,
                        mime="application/zip",
                    )

                    st.success("Raporty wygenerowane!")

            except Exception as e:
                st.error(f"Blad generowania: {e}")

    # Podglad raportu glownego
    st.markdown("---")
    st.subheader("Podglad danych")

    if has_quality:
        with st.expander("Data Quality", expanded=False):
            qr = st.session_state.quality_result
            st.write(f"- **Quality Score:** {qr.quality_score:.1f}%")
            st.write(f"- **Rekordow:** {qr.total_records}")
            st.write(f"- **Poprawnych:** {qr.valid_records}")
            st.write(f"- **Imputowanych:** {qr.imputed_records}")

            st.markdown("**Pokrycie danych po imputacji:**")
            st.write(f"- Wymiary: {qr.metrics_after.dimensions_coverage_pct:.1f}%")
            st.write(f"- Waga: {qr.metrics_after.weight_coverage_pct:.1f}%")

    if has_capacity:
        with st.expander("Capacity Analysis", expanded=False):
            cr = st.session_state.capacity_result
            st.write(f"- **Total SKU:** {cr.total_sku}")
            st.write(f"- **FIT:** {cr.fit_count}")
            st.write(f"- **BORDERLINE:** {cr.borderline_count}")
            st.write(f"- **NOT_FIT:** {cr.not_fit_count}")
            st.write(f"- **Fit %:** {cr.fit_percentage:.1f}%")
            st.write(f"- **Nosniki:** {', '.join(cr.carriers_analyzed)}")

    if has_performance:
        with st.expander("Performance Analysis", expanded=False):
            pr = st.session_state.performance_result
            kpi = pr.kpi
            st.write(f"- **Linii:** {kpi.total_lines}")
            st.write(f"- **Zamowien:** {kpi.total_orders}")
            st.write(f"- **Units:** {kpi.total_units}")
            st.write(f"- **Avg lines/h:** {kpi.avg_lines_per_hour:.1f}")
            st.write(f"- **Peak lines/h:** {kpi.peak_lines_per_hour}")
            st.write(f"- **P95 lines/h:** {kpi.p95_lines_per_hour:.1f}")


def main() -> None:
    """Glowna funkcja aplikacji."""
    init_session_state()
    render_sidebar()
    render_tabs()


if __name__ == "__main__":
    main()
