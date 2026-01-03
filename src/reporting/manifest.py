"""Generowanie Manifest.json z SHA256 dla plikow."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class ManifestGenerator:
    """Generator manifestu z sumami kontrolnymi."""

    def __init__(self) -> None:
        """Inicjalizacja generatora."""
        pass

    def calculate_sha256(self, file_path: Path) -> str:
        """Oblicz SHA256 dla pliku."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate(
        self,
        output_path: Path,
        files: list[Path],
        client_name: str = "",
        run_id: Optional[str] = None,
    ) -> Path:
        """Generuj manifest.

        Args:
            output_path: Sciezka do pliku manifestu
            files: Lista plikow do uwzglednienia
            client_name: Nazwa klienta
            run_id: Identyfikator uruchomienia

        Returns:
            Sciezka do wygenerowanego manifestu
        """
        manifest = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "client": client_name,
            "run_id": run_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "files": [],
        }

        for file_path in files:
            if file_path.exists():
                file_info = {
                    "name": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "sha256": self.calculate_sha256(file_path),
                }
                manifest["files"].append(file_info)

        manifest["total_files"] = len(manifest["files"])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return output_path


def generate_manifest(
    output_path: Path,
    files: list[Path],
    **kwargs,
) -> Path:
    """Funkcja pomocnicza do generowania manifestu.

    Args:
        output_path: Sciezka do pliku manifestu
        files: Lista plikow
        **kwargs: Dodatkowe argumenty

    Returns:
        Sciezka do wygenerowanego manifestu
    """
    generator = ManifestGenerator()
    return generator.generate(output_path, files, **kwargs)
