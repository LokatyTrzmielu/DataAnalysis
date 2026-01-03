"""Glowna aplikacja Streamlit DataAnalysis."""

import streamlit as st
from pathlib import Path

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


def render_import_tab() -> None:
    """Zakladka Import."""
    st.header("Import danych")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masterdata")
        masterdata_file = st.file_uploader(
            "Wybierz plik Masterdata",
            type=["xlsx", "csv", "txt"],
            key="masterdata_upload",
        )

        if masterdata_file is not None:
            if st.button("Importuj Masterdata", key="import_md"):
                with st.spinner("Importowanie..."):
                    try:
                        import tempfile
                        from src.ingest import ingest_masterdata

                        # Zapisz do pliku tymczasowego
                        suffix = Path(masterdata_file.name).suffix
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(masterdata_file.read())
                            tmp_path = tmp.name

                        result = ingest_masterdata(tmp_path)
                        st.session_state.masterdata_df = result.df

                        st.success(f"Zaimportowano {result.rows_imported} wierszy")

                        if result.warnings:
                            for warning in result.warnings:
                                st.warning(warning)

                        # Podglad
                        st.dataframe(result.df.head(10).to_pandas(), use_container_width=True)

                    except Exception as e:
                        st.error(f"Blad importu: {e}")

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


def render_analysis_tab() -> None:
    """Zakladka Analiza."""
    st.header("Analiza pojemnosciowa i wydajnosciowa")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Analiza pojemnosciowa")

        if st.session_state.masterdata_df is None:
            st.info("Zaimportuj Masterdata")
        elif st.button("Uruchom analize pojemnosciowa"):
            with st.spinner("Analiza w toku..."):
                try:
                    from src.analytics import analyze_capacity
                    from src.core.types import CarrierConfig

                    # Domyslne nosniki
                    carriers = [
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
                    ]

                    result = analyze_capacity(st.session_state.masterdata_df, carriers)
                    st.session_state.capacity_result = result

                    st.success("Analiza pojemnosciowa zakonczona")

                    # Wyniki
                    st.metric("FIT", result.fit_count)
                    st.metric("BORDERLINE", result.borderline_count)
                    st.metric("NOT FIT", result.not_fit_count)
                    st.metric("Fit %", f"{result.fit_percentage:.1f}%")

                except Exception as e:
                    st.error(f"Blad: {e}")

    with col2:
        st.subheader("Analiza wydajnosciowa")

        if st.session_state.orders_df is None:
            st.info("Zaimportuj Orders")
        elif st.button("Uruchom analize wydajnosciowa"):
            with st.spinner("Analiza w toku..."):
                try:
                    from src.analytics import analyze_performance

                    result = analyze_performance(st.session_state.orders_df)
                    st.session_state.performance_result = result
                    st.session_state.analysis_complete = True

                    st.success("Analiza wydajnosciowa zakonczona")

                    kpi = result.kpi
                    st.metric("Linii/h (avg)", f"{kpi.avg_lines_per_hour:.1f}")
                    st.metric("Zamowien/h (avg)", f"{kpi.avg_orders_per_hour:.1f}")
                    st.metric("Peak linii/h", kpi.peak_lines_per_hour)
                    st.metric("P95 linii/h", f"{kpi.p95_lines_per_hour:.1f}")

                except Exception as e:
                    st.error(f"Blad: {e}")


def render_reports_tab() -> None:
    """Zakladka Raporty."""
    st.header("Generowanie raportow")

    if not st.session_state.get("analysis_complete"):
        st.info("Najpierw przeprowadz analize w zakladce Analiza")
        return

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
    if st.session_state.quality_result or st.session_state.performance_result:
        st.markdown("---")
        st.subheader("Podglad raportu")

        if st.session_state.quality_result:
            qr = st.session_state.quality_result
            st.write("**Data Quality:**")
            st.write(f"- Quality Score: {qr.quality_score:.1f}%")
            st.write(f"- Rekordow: {qr.total_records}")
            st.write(f"- Imputowanych: {qr.imputed_records}")

        if st.session_state.performance_result:
            pr = st.session_state.performance_result
            kpi = pr.kpi
            st.write("**Performance:**")
            st.write(f"- Linii: {kpi.total_lines}")
            st.write(f"- Zamowien: {kpi.total_orders}")
            st.write(f"- Avg lines/h: {kpi.avg_lines_per_hour:.1f}")


def main() -> None:
    """Glowna funkcja aplikacji."""
    init_session_state()
    render_sidebar()
    render_tabs()


if __name__ == "__main__":
    main()
