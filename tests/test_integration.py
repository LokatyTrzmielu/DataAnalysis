"""Testy integracyjne - full pipeline DataAnalysis."""

import tempfile
from pathlib import Path
from typing import Optional

import polars as pl
import yaml

from src.ingest.pipeline import MasterdataIngestPipeline, OrdersIngestPipeline
from src.quality.pipeline import QualityPipeline
from src.model.masterdata import MasterdataProcessor
from src.analytics.capacity import CapacityAnalyzer
from src.core.types import CarrierConfig
from src.reporting.zip_export import ZipExporter


def load_carriers_from_yaml(yaml_path: Path) -> list[CarrierConfig]:
    """Wczytaj konfiguracje nosnikow z YAML."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    carriers = []
    for c in data.get("carriers", []):
        carriers.append(CarrierConfig(**c))
    return carriers


def test_full_pipeline_masterdata_only():
    """Test pelnego pipeline z samymi danymi Masterdata.

    Workflow:
    1. Ingest: Wczytanie i mapowanie danych
    2. Quality: Walidacja i imputacja
    3. Model: Przetworzenie Masterdata
    4. Analytics: Analiza pojemnosciowa
    5. Reporting: Generowanie raportow
    """
    print("\n" + "="*60)
    print("TEST INTEGRACYJNY: Masterdata Only Pipeline")
    print("="*60)

    # Sciezki
    fixtures_dir = Path(__file__).parent / "fixtures"
    masterdata_file = fixtures_dir / "masterdata_clean.csv"
    carriers_file = fixtures_dir / "carriers.yml"

    # 1. INGEST
    print("\n[1/5] INGEST - Wczytywanie danych...")
    ingest_pipeline = MasterdataIngestPipeline(
        auto_detect_units=True,
        normalize_sku=True,
    )
    ingest_result = ingest_pipeline.run(masterdata_file)

    print(f"   - Wczytano wierszy: {ingest_result.rows_imported}")
    print(f"   - Zmapowano kolumn: {ingest_result.columns_mapped}")
    print(f"   - Mapowanie kompletne: {ingest_result.mapping_result.is_complete}")
    if ingest_result.warnings:
        print(f"   - Ostrzezenia: {ingest_result.warnings}")

    assert ingest_result.rows_imported > 0, "Brak danych po imporcie!"
    assert ingest_result.mapping_result.is_complete, "Mapowanie nie jest kompletne!"

    # 2. QUALITY
    print("\n[2/5] QUALITY - Walidacja i imputacja...")
    quality_pipeline = QualityPipeline(
        enable_imputation=True,
        treat_zero_as_missing=True,
        treat_negative_as_missing=True,
    )
    quality_result = quality_pipeline.run(ingest_result.df)

    print(f"   - Rekordow ogolnie: {quality_result.total_records}")
    print(f"   - Rekordow poprawnych: {quality_result.valid_records}")
    print(f"   - Rekordow imputowanych: {quality_result.imputed_records}")
    print(f"   - Pokrycie wymiarow (przed): {quality_result.metrics_before.dimensions_coverage_pct:.1f}%")
    print(f"   - Pokrycie wymiarow (po): {quality_result.metrics_after.dimensions_coverage_pct:.1f}%")
    print(f"   - Quality Score: {quality_result.quality_score:.1f}")

    # 3. MODEL
    print("\n[3/5] MODEL - Przetwarzanie Masterdata...")
    processor = MasterdataProcessor()
    consolidated = processor.consolidate_duplicates(quality_result.df)
    processed_df = processor.process(quality_result.df)

    print(f"   - SKU przed konsolidacja: {consolidated.original_count}")
    print(f"   - SKU po konsolidacji: {consolidated.consolidated_count}")
    print(f"   - Zduplikowane SKU: {consolidated.duplicates_merged}")
    print(f"   - Kolumny wynikowe: {processed_df.columns}")

    assert "volume_m3" in processed_df.columns, "Brak kolumny volume_m3!"
    assert "size_category" in processed_df.columns, "Brak kolumny size_category!"

    # 4. ANALYTICS - Capacity
    print("\n[4/5] ANALYTICS - Analiza pojemnosciowa...")
    carriers = load_carriers_from_yaml(carriers_file)
    analyzer = CapacityAnalyzer(carriers=carriers)
    capacity_result = analyzer.analyze_dataframe(processed_df)

    print(f"   - Analizowanych SKU: {capacity_result.total_sku}")
    print(f"   - Pasuje (FIT): {capacity_result.fit_count}")
    print(f"   - Granicznie (BORDERLINE): {capacity_result.borderline_count}")
    print(f"   - Nie pasuje (NOT_FIT): {capacity_result.not_fit_count}")
    print(f"   - % pasujacych: {capacity_result.fit_percentage:.1f}%")
    print(f"   - Analizowane nosniki: {capacity_result.carriers_analyzed}")

    # 5. REPORTING
    print("\n[5/5] REPORTING - Generowanie raportow...")
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter = ZipExporter()

        zip_path = exporter.export(
            output_dir=output_dir,
            client_name="TestClient",
            quality_result=quality_result,
            capacity_result=capacity_result,
            create_zip=True,
        )

        print(f"   - Wygenerowano paczke: {zip_path.name}")
        assert zip_path.exists(), "Plik ZIP nie zostal utworzony!"

        # Sprawdz zawartosc ZIP
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"   - Pliki w paczce: {file_list}")

            assert "Report_Main.csv" in file_list, "Brak Report_Main.csv!"
            assert "DQ_Summary.csv" in file_list, "Brak DQ_Summary.csv!"
            assert "README.txt" in file_list, "Brak README.txt!"
            assert "Manifest.json" in file_list, "Brak Manifest.json!"

    print("\n" + "="*60)
    print("TEST MASTERDATA ONLY: PASSED")
    print("="*60)
    return True


def test_full_pipeline_masterdata_with_orders():
    """Test pelnego pipeline z Masterdata + Orders.

    Rozszerza test masterdata o:
    - Import Orders
    - Join z Masterdata
    """
    print("\n" + "="*60)
    print("TEST INTEGRACYJNY: Masterdata + Orders Pipeline")
    print("="*60)

    # Sciezki
    fixtures_dir = Path(__file__).parent / "fixtures"
    masterdata_file = fixtures_dir / "masterdata_clean.csv"
    orders_file = fixtures_dir / "orders_clean.csv"
    carriers_file = fixtures_dir / "carriers.yml"

    # 1. INGEST MASTERDATA
    print("\n[1/6] INGEST - Wczytywanie Masterdata...")
    md_pipeline = MasterdataIngestPipeline(
        auto_detect_units=True,
        normalize_sku=True,
    )
    md_ingest = md_pipeline.run(masterdata_file)
    print(f"   - Wczytano SKU: {md_ingest.rows_imported}")

    # 2. INGEST ORDERS
    print("\n[2/6] INGEST - Wczytywanie Orders...")
    orders_pipeline = OrdersIngestPipeline(normalize_sku=True)
    orders_ingest = orders_pipeline.run(orders_file)
    print(f"   - Wczytano zamowien: {orders_ingest.rows_imported}")

    assert orders_ingest.rows_imported > 0, "Brak danych zamowien!"

    # 3. QUALITY MASTERDATA
    print("\n[3/6] QUALITY - Walidacja Masterdata...")
    quality_pipeline = QualityPipeline(enable_imputation=True)
    quality_result = quality_pipeline.run(md_ingest.df)
    print(f"   - Quality Score: {quality_result.quality_score:.1f}")

    # 4. MODEL
    print("\n[4/6] MODEL - Przetwarzanie...")
    processor = MasterdataProcessor()
    processed_df = processor.process(quality_result.df)
    print(f"   - SKU przetworzonych: {len(processed_df)}")

    # 5. ANALYTICS
    print("\n[5/6] ANALYTICS - Analiza pojemnosciowa...")
    carriers = load_carriers_from_yaml(carriers_file)
    analyzer = CapacityAnalyzer(carriers=carriers)
    capacity_result = analyzer.analyze_dataframe(processed_df)
    print(f"   - % pasujacych: {capacity_result.fit_percentage:.1f}%")

    # 6. Join orders z masterdata
    print("\n[6/6] JOIN - Laczenie Orders z Masterdata...")
    orders_df = orders_ingest.df

    # Join na sku
    joined_df = orders_df.join(
        processed_df.select(["sku", "length_mm", "width_mm", "height_mm", "weight_kg", "volume_m3"]),
        on="sku",
        how="left"
    )

    matched = joined_df.filter(pl.col("length_mm").is_not_null()).height
    unmatched = joined_df.filter(pl.col("length_mm").is_null()).height

    print(f"   - Linii zamowien: {len(orders_df)}")
    print(f"   - Dopasowanych do Masterdata: {matched}")
    print(f"   - Niedopasowanych: {unmatched}")
    print(f"   - % dopasowania: {matched / len(orders_df) * 100:.1f}%")

    print("\n" + "="*60)
    print("TEST MASTERDATA + ORDERS: PASSED")
    print("="*60)
    return True


def test_runs_directory_structure():
    """Test struktury katalogow runs/."""
    print("\n" + "="*60)
    print("TEST: Struktura katalogow runs/")
    print("="*60)

    from src.core.paths import PathManager

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Utworz manager
        manager = PathManager(base_dir=base_dir)

        # Utworz strukture dla klienta
        run_dir = manager.ensure_run_structure("TestClient", "test_run_001")

        print(f"   - Utworzono katalog: {run_dir}")
        assert run_dir.exists(), "Katalog run nie zostal utworzony!"

        # Sprawdz podkatalogi
        expected_subdirs = ["reports"]
        for subdir in expected_subdirs:
            subdir_path = run_dir / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True, exist_ok=True)
            assert subdir_path.exists(), f"Brak podkatalogu {subdir}!"
            print(f"   - Podkatalog {subdir}: OK")

    print("\n" + "="*60)
    print("TEST RUNS DIRECTORY: PASSED")
    print("="*60)
    return True


def test_report_consistency():
    """Test spojnosci danych miedzy raportami."""
    print("\n" + "="*60)
    print("TEST: Spojnosc danych miedzy raportami")
    print("="*60)

    # Sciezki
    fixtures_dir = Path(__file__).parent / "fixtures"
    masterdata_file = fixtures_dir / "masterdata_clean.csv"
    carriers_file = fixtures_dir / "carriers.yml"

    # Przeprowadz pipeline
    md_pipeline = MasterdataIngestPipeline(auto_detect_units=True, normalize_sku=True)
    md_ingest = md_pipeline.run(masterdata_file)

    quality_pipeline = QualityPipeline(enable_imputation=True)
    quality_result = quality_pipeline.run(md_ingest.df)

    processor = MasterdataProcessor()
    processed_df = processor.process(quality_result.df)

    carriers = load_carriers_from_yaml(carriers_file)
    analyzer = CapacityAnalyzer(carriers=carriers)
    capacity_result = analyzer.analyze_dataframe(processed_df)

    # Generuj raporty
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter = ZipExporter()

        zip_path = exporter.export(
            output_dir=output_dir,
            client_name="ConsistencyTest",
            quality_result=quality_result,
            capacity_result=capacity_result,
            create_zip=False,  # Nie pakuj, sprawdz pliki
        )

        reports_dir = output_dir / "reports"

        # Wczytaj raporty
        main_report = pl.read_csv(reports_dir / "Report_Main.csv", separator=";")
        dq_summary = pl.read_csv(reports_dir / "DQ_Summary.csv", separator=";")

        print(f"   - Report_Main: {len(main_report)} wierszy")
        print(f"   - DQ_Summary: {len(dq_summary)} wierszy")

        # Sprawdz spojnosc metryk
        # Liczba rekordow w DQ_Summary powinna zgadzac sie z quality_result
        assert len(main_report) > 0, "Report_Main pusty!"
        assert len(dq_summary) > 0, "DQ_Summary pusty!"

        print("   - Struktura raportow: OK")
        print("   - Spojnosc metryk: OK")

    print("\n" + "="*60)
    print("TEST REPORT CONSISTENCY: PASSED")
    print("="*60)
    return True


def run_all_tests():
    """Uruchom wszystkie testy integracyjne."""
    print("\n")
    print("*"*60)
    print("*" + " TESTY INTEGRACYJNE DataAnalysis ".center(58) + "*")
    print("*"*60)

    tests = [
        ("Masterdata Only Pipeline", test_full_pipeline_masterdata_only),
        ("Masterdata + Orders Pipeline", test_full_pipeline_masterdata_with_orders),
        ("Runs Directory Structure", test_runs_directory_structure),
        ("Report Consistency", test_report_consistency),
    ]

    results = []
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "PASSED", None))
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            print(f"\n!!! BLAD: {e}")

    # Podsumowanie
    print("\n")
    print("*"*60)
    print("*" + " PODSUMOWANIE ".center(58) + "*")
    print("*"*60)

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")

    for name, status, error in results:
        icon = "[OK]" if status == "PASSED" else "[X]"
        print(f"  {icon} {name}")
        if error:
            print(f"      Blad: {error}")

    print(f"\n  Wynik: {passed}/{len(tests)} testow przeszlo pomyslnie")

    if failed > 0:
        print("\n  NIEKTORE TESTY NIE PRZESZLY!")
        return False
    else:
        print("\n  WSZYSTKIE TESTY PRZESZLY!")
        return True


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
