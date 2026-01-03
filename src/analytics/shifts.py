"""Parsowanie i obsluga harmonogramow zmian."""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Optional
from pathlib import Path

import yaml

from src.core.types import ShiftConfig, ShiftType, WeeklySchedule
from src.core.config import DEFAULT_PRODUCTIVE_HOURS_PER_SHIFT


@dataclass
class ShiftInstance:
    """Konkretna instancja zmiany (z data)."""
    date: date
    name: str
    start: time
    end: time
    shift_type: ShiftType
    productive_hours: float

    @property
    def duration_hours(self) -> float:
        """Czas trwania zmiany w godzinach."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60
        return (end_minutes - start_minutes) / 60


@dataclass
class ShiftSchedule:
    """Pelny harmonogram zmian z exceptions."""
    weekly_schedule: WeeklySchedule
    exceptions: list[dict] = field(default_factory=list)

    def get_shifts_for_date(self, dt: date) -> list[ShiftInstance]:
        """Pobierz zmiany dla konkretnej daty."""
        weekday = dt.weekday()
        base_shifts = self.weekly_schedule.get_shifts_for_day(weekday)

        # Konwertuj na ShiftInstance
        instances = []
        for shift in base_shifts:
            instances.append(ShiftInstance(
                date=dt,
                name=shift.name,
                start=shift.start,
                end=shift.end,
                shift_type=shift.shift_type,
                productive_hours=self.weekly_schedule.productive_hours_per_shift,
            ))

        # Dodaj overlay shifts z exceptions
        for exc in self.exceptions:
            if self._exception_applies(exc, dt):
                overlay_shifts = self._get_exception_shifts(exc, weekday)
                for shift in overlay_shifts:
                    instances.append(ShiftInstance(
                        date=dt,
                        name=shift["name"],
                        start=self._parse_time(shift["start"]),
                        end=self._parse_time(shift["end"]),
                        shift_type=ShiftType(shift.get("shift_type", "overlay")),
                        productive_hours=self.weekly_schedule.productive_hours_per_shift,
                    ))

        return instances

    def _exception_applies(self, exc: dict, dt: date) -> bool:
        """Sprawdz czy exception dotyczy daty."""
        exc_type = exc.get("type", "")

        if exc_type == "date_overlay":
            exc_date = datetime.strptime(exc["date"], "%Y-%m-%d").date()
            return exc_date == dt

        elif exc_type == "range_overlay":
            from_date = datetime.strptime(exc["from"], "%Y-%m-%d").date()
            to_date = datetime.strptime(exc["to"], "%Y-%m-%d").date()
            return from_date <= dt <= to_date

        return False

    def _get_exception_shifts(self, exc: dict, weekday: int) -> list[dict]:
        """Pobierz zmiany z exception."""
        if "add_shifts" in exc:
            return exc["add_shifts"]

        if "add_shifts_by_weekday" in exc:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = day_names[weekday]
            return exc["add_shifts_by_weekday"].get(day_name, [])

        return []

    def _parse_time(self, time_str: str) -> time:
        """Parsuj czas z stringa."""
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return datetime.strptime(time_str, "%H:%M:%S").time()

    def get_shifts_for_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[ShiftInstance]:
        """Pobierz wszystkie zmiany dla zakresu dat."""
        all_shifts = []
        current = start_date

        while current <= end_date:
            all_shifts.extend(self.get_shifts_for_date(current))
            current += timedelta(days=1)

        return all_shifts

    def calculate_total_hours(
        self,
        start_date: date,
        end_date: date,
        shift_type: Optional[ShiftType] = None,
    ) -> float:
        """Oblicz calkowita liczbe godzin w zakresie."""
        shifts = self.get_shifts_for_range(start_date, end_date)

        if shift_type:
            shifts = [s for s in shifts if s.shift_type == shift_type]

        return sum(s.productive_hours for s in shifts)


class ShiftScheduleLoader:
    """Loader harmonogramow z plikow YAML."""

    @staticmethod
    def load_from_file(file_path: str | Path) -> ShiftSchedule:
        """Wczytaj harmonogram z pliku YAML."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return ShiftScheduleLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(data: dict) -> ShiftSchedule:
        """Wczytaj harmonogram ze slownika."""
        # Parsuj weekly schedule
        weekly_data = data.get("weekly_schedule", {})
        day_mapping = {
            "Mon": "mon", "Tue": "tue", "Wed": "wed",
            "Thu": "thu", "Fri": "fri", "Sat": "sat", "Sun": "sun"
        }

        weekly_shifts = {}
        for day_key, day_attr in day_mapping.items():
            shifts_data = weekly_data.get(day_key, [])
            shifts = []
            for s in shifts_data:
                shifts.append(ShiftConfig(
                    name=s["name"],
                    start=s["start"],
                    end=s["end"],
                    shift_type=ShiftType(s.get("shift_type", "base")),
                ))
            weekly_shifts[day_attr] = shifts

        weekly = WeeklySchedule(
            timezone=data.get("timezone", "Europe/Warsaw"),
            productive_hours_per_shift=data.get("productive_hours", {}).get(
                "default_per_shift", DEFAULT_PRODUCTIVE_HOURS_PER_SHIFT
            ),
            **weekly_shifts,
        )

        exceptions = data.get("exceptions", [])

        return ShiftSchedule(
            weekly_schedule=weekly,
            exceptions=exceptions,
        )


def load_shifts(file_path: str | Path) -> ShiftSchedule:
    """Funkcja pomocnicza do wczytania harmonogramu.

    Args:
        file_path: Sciezka do pliku YAML

    Returns:
        ShiftSchedule
    """
    return ShiftScheduleLoader.load_from_file(file_path)
