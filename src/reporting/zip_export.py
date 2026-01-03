"""Eksport paczki raportow do ZIP."""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.quality.pipeline import QualityPipelineResult
from src.analytics.capacity import CapacityAnalysisResult
from src.analytics.performance import PerformanceAnalysisResult
from src.reporting.csv_writer import CSVWriter
from src.reporting.main_report import MainReportGenerator
from src.reporting.dq_reports import DQReportGenerator
from src.reporting.manifest import ManifestGenerator
from src.reporting.readme import ReadmeGenerator


class ZipExporter:
    """Eksporter paczki raportow do ZIP."""

    def __init__(self) -> None:
        """Inicjalizacja eksportera."""
        self.csv_writer = CSVWriter()
        self.main_generator = MainReportGenerator()
        self.dq_generator = DQReportGenerator()
        self.manifest_generator = ManifestGenerator()
        self.readme_generator = ReadmeGenerator()

    def export(
        self,
        output_dir: Path,
        client_name: str,
        quality_result: Optional[QualityPipelineResult] = None,
        capacity_result: Optional[CapacityAnalysisResult] = None,
        performance_result: Optional[PerformanceAnalysisResult] = None,
        run_id: Optional[str] = None,
        create_zip: bool = True,
    ) -> Path:
        """Eksportuj pelna paczke raportow.

        Args:
            output_dir: Katalog wynikowy
            client_name: Nazwa klienta
            quality_result: Wyniki jakosci danych
            capacity_result: Wyniki analizy pojemnosciowej
            performance_result: Wyniki analizy wydajnosciowej
            run_id: Identyfikator uruchomienia
            create_zip: Czy utworzyc plik ZIP

        Returns:
            Sciezka do paczki (ZIP lub katalog)
        """
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        reports_dir = output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        generated_files: list[Path] = []

        # 1. Glowny raport
        main_report_path = reports_dir / "Report_Main.csv"
        self.main_generator.generate(
            main_report_path,
            quality_result=quality_result,
            capacity_result=capacity_result,
            performance_result=performance_result,
            client_name=client_name,
        )
        generated_files.append(main_report_path)

        # 2. Raporty DQ
        if quality_result:
            dq_paths = self.dq_generator.generate_all(
                reports_dir,
                quality_result.metrics_after,
                quality_result.dq_lists,
            )
            generated_files.extend(dq_paths)

        # 3. README
        readme_path = reports_dir / "README.txt"
        self.readme_generator.generate(
            readme_path,
            generated_files,
            client_name=client_name,
            run_id=run_id,
        )
        generated_files.append(readme_path)

        # 4. Manifest
        manifest_path = reports_dir / "Manifest.json"
        self.manifest_generator.generate(
            manifest_path,
            generated_files,
            client_name=client_name,
            run_id=run_id,
        )
        generated_files.append(manifest_path)

        # 5. Utworz ZIP
        if create_zip:
            zip_name = f"{client_name}_{run_id}.zip" if client_name else f"report_{run_id}.zip"
            zip_path = output_dir / zip_name

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in generated_files:
                    zf.write(file_path, file_path.name)

            return zip_path

        return reports_dir


def export_reports(
    output_dir: Path,
    client_name: str,
    **kwargs,
) -> Path:
    """Funkcja pomocnicza do eksportu raportow.

    Args:
        output_dir: Katalog wynikowy
        client_name: Nazwa klienta
        **kwargs: Dodatkowe argumenty

    Returns:
        Sciezka do paczki
    """
    exporter = ZipExporter()
    return exporter.export(output_dir, client_name, **kwargs)
