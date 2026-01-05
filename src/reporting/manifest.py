"""Generate Manifest.json with SHA256 checksums for files."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class ManifestGenerator:
    """Manifest generator with checksums."""

    def __init__(self) -> None:
        """Initialize the generator."""
        pass

    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 for a file."""
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
        """Generate manifest.

        Args:
            output_path: Path to the manifest file
            files: List of files to include
            client_name: Client name
            run_id: Run identifier

        Returns:
            Path to the generated manifest
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
    """Helper function to generate manifest.

    Args:
        output_path: Path to the manifest file
        files: List of files
        **kwargs: Additional arguments

    Returns:
        Path to the generated manifest
    """
    generator = ManifestGenerator()
    return generator.generate(output_path, files, **kwargs)
