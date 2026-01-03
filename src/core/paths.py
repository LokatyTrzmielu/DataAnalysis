"""Zarzadzanie sciezkami projektu i klientow."""

from pathlib import Path
from datetime import datetime
from typing import Optional


class PathManager:
    """Zarzadzanie sciezkami dla runs/ i wynikow analiz."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """Inicjalizacja PathManager.

        Args:
            base_dir: Glowny katalog projektu. Jesli None, uzywa katalogu biezacego.
        """
        if base_dir is None:
            # Znajdz katalog projektu (gdzie jest pyproject.toml)
            current = Path.cwd()
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    base_dir = current
                    break
                current = current.parent
            else:
                base_dir = Path.cwd()

        self._base_dir = Path(base_dir)
        self._runs_dir = self._base_dir / "runs"

    @property
    def base_dir(self) -> Path:
        """Glowny katalog projektu."""
        return self._base_dir

    @property
    def runs_dir(self) -> Path:
        """Katalog z wynikami analiz per klient."""
        return self._runs_dir

    @property
    def src_dir(self) -> Path:
        """Katalog zrodlowy aplikacji."""
        return self._base_dir / "src"

    @property
    def tests_dir(self) -> Path:
        """Katalog testow."""
        return self._base_dir / "tests"

    @property
    def fixtures_dir(self) -> Path:
        """Katalog z danymi testowymi."""
        return self.tests_dir / "fixtures"

    def get_client_dir(self, client_name: str) -> Path:
        """Pobierz katalog dla danego klienta.

        Args:
            client_name: Nazwa klienta (bezpieczna dla systemu plikow)

        Returns:
            Sciezka do katalogu klienta w runs/
        """
        safe_name = self._sanitize_name(client_name)
        return self._runs_dir / safe_name

    def get_run_dir(self, client_name: str, run_id: Optional[str] = None) -> Path:
        """Pobierz katalog dla konkretnego uruchomienia analizy.

        Args:
            client_name: Nazwa klienta
            run_id: Identyfikator uruchomienia. Jesli None, generuje timestamp.

        Returns:
            Sciezka do katalogu uruchomienia
        """
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        return self.get_client_dir(client_name) / run_id

    def get_staging_dir(self, client_name: str, run_id: str) -> Path:
        """Katalog staging dla plikow Parquet."""
        return self.get_run_dir(client_name, run_id) / "staging"

    def get_reports_dir(self, client_name: str, run_id: str) -> Path:
        """Katalog raportow CSV."""
        return self.get_run_dir(client_name, run_id) / "reports"

    def ensure_run_structure(self, client_name: str, run_id: Optional[str] = None) -> Path:
        """Utworz pelna strukture katalogow dla uruchomienia.

        Args:
            client_name: Nazwa klienta
            run_id: Identyfikator uruchomienia

        Returns:
            Sciezka do katalogu uruchomienia
        """
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        run_dir = self.get_run_dir(client_name, run_id)

        # Utworz strukture
        (run_dir / "staging").mkdir(parents=True, exist_ok=True)
        (run_dir / "reports").mkdir(parents=True, exist_ok=True)

        return run_dir

    def list_clients(self) -> list[str]:
        """Lista wszystkich klientow z katalogu runs/."""
        if not self._runs_dir.exists():
            return []
        return [d.name for d in self._runs_dir.iterdir() if d.is_dir()]

    def list_runs(self, client_name: str) -> list[str]:
        """Lista wszystkich uruchomien dla klienta."""
        client_dir = self.get_client_dir(client_name)
        if not client_dir.exists():
            return []
        return sorted([d.name for d in client_dir.iterdir() if d.is_dir()], reverse=True)

    def get_latest_run(self, client_name: str) -> Optional[Path]:
        """Pobierz najnowsze uruchomienie dla klienta."""
        runs = self.list_runs(client_name)
        if not runs:
            return None
        return self.get_run_dir(client_name, runs[0])

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Usun niebezpieczne znaki z nazwy.

        Args:
            name: Oryginalna nazwa

        Returns:
            Bezpieczna nazwa dla systemu plikow
        """
        # Zamien spacje na podkreslniki
        safe = name.replace(" ", "_")
        # Usun znaki specjalne
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        safe = "".join(c for c in safe if c in allowed)
        # Ogranicz dlugosc
        return safe[:50] if len(safe) > 50 else safe
