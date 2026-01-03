
import streamlit as st
import os
from ingest.ingest import import_and_convert_to_parquet
from validation.validation import validate_missing_values, imputuj_braki_medianą
from analytics.analytics import calculate_kpi, fit_check, performance_analysis_with_shifts
from reporting.reporting import generate_main_report, generate_data_quality_scorecard, generate_reports_package

st.set_page_config(page_title="DataAnalysis", layout="wide")
st.title("DataAnalysis – Analiza Masterdata & Orders")

# Folder roboczy
WORK_DIR = "output"
os.makedirs(WORK_DIR, exist_ok=True)

# Upload plików
st.header("📂 Wgraj pliki")
masterdata_file = st.file_uploader("Plik Masterdata", type=["csv", "xlsx"])
orders_file = st.file_uploader("Plik Orders", type=["csv", "xlsx"])

if masterdata_file:
    masterdata_path = os.path.join(WORK_DIR, "masterdata.parquet")
    import_and_convert_to_parquet(masterdata_file, masterdata_path)
    st.success(f"Masterdata zapisane jako {masterdata_path}")

if orders_file:
    orders_path = os.path.join(WORK_DIR, "orders.parquet")
    import_and_convert_to_parquet(orders_file, orders_path)
    st.success(f"Orders zapisane jako {orders_path}")

# Sidebar – konfiguracja
st.sidebar.header("⚙️ Parametry analizy")
borderline_threshold = st.sidebar.number_input("Borderline threshold (mm)", value=2.0)
max_dims = (
    st.sidebar.number_input("Max długość (mm)", value=600),
    st.sidebar.number_input("Max szerokość (mm)", value=400),
    st.sidebar.number_input("Max wysokość (mm)", value=300)
)
max_weight = st.sidebar.number_input("Max waga (kg)", value=30.0)
shifts = {"Zmiana 1": (6, 14), "Zmiana 2": (14, 22)}

# Sekcja analizy
st.header("🔍 Analiza danych")

if st.button("Walidacja danych"):
    if masterdata_file:
        report_path = os.path.join(WORK_DIR, "raport_brakow.csv")
        st.write(validate_missing_values(masterdata_path, report_path))
        st.success("Raport braków wygenerowany.")
    else:
        st.error("Wgraj plik Masterdata.")

if st.button("Imputacja braków"):
    if masterdata_file:
        imputuj_braki_medianą(masterdata_path, WORK_DIR)
        st.success("Braki uzupełnione medianą.")
    else:
        st.error("Wgraj plik Masterdata.")

if st.button("Analiza gabarytowa (Fit-Check)"):
    if masterdata_file:
        fit_report = os.path.join(WORK_DIR, "raport_fit.csv")
        fit_check(masterdata_path, fit_report, max_dims, max_weight, borderline_threshold)
        st.success("Raport dopasowania wygenerowany.")
    else:
        st.error("Wgraj plik Masterdata.")

if st.button("Analiza wydajnościowa"):
    if orders_file:
        perf_report = os.path.join(WORK_DIR, "raport_performance.csv")
        performance_analysis_with_shifts(orders_path, shifts, perf_report)
        st.success("Raport wydajnościowy wygenerowany.")
    else:
        st.error("Wgraj plik Orders.")

if st.button("Raport Data Quality"):
    if masterdata_file:
        dq_report = os.path.join(WORK_DIR, "data_quality_scorecard.csv")
        generate_data_quality_scorecard(masterdata_path, dq_report)
        st.success("Raport Data Quality wygenerowany.")
    else:
        st.error("Wgraj plik Masterdata.")

if st.button("Pobierz paczkę raportów"):
    report_files = [
        os.path.join(WORK_DIR, "raport_brakow.csv"),
        os.path.join(WORK_DIR, "raport_fit.csv"),
        os.path.join(WORK_DIR, "raport_performance.csv"),
        os.path.join(WORK_DIR, "data_quality_scorecard.csv")
    ]
    zip_path = os.path.join(WORK_DIR, "raporty_analizy.zip")
    generate_reports_package(report_files, zip_path)
    st.success(f"Paczka raportów utworzona: {zip_path}")
    st.download_button("📥 Pobierz ZIP", data=open(zip_path, "rb"), file_name="raporty_analizy.zip")
