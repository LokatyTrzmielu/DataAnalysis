"""Formatowanie liczb dla raportow CSV zgodnie z wymaganiami."""

from datetime import date, datetime
from typing import Union

from src.core.config import (
    DECIMAL_PLACES_VOLUME_M3,
    DECIMAL_PLACES_WEIGHT_KG,
    DECIMAL_PLACES_PERCENT,
    DECIMAL_PLACES_RATE,
    DECIMAL_PLACES_AVERAGE,
    DECIMAL_PLACES_RATIO,
    DATE_FORMAT,
    DATETIME_FORMAT,
)


class Formatter:
    """Formatowanie wartosci dla raportow CSV."""

    @staticmethod
    def volume_m3(value: float) -> str:
        """Formatuj objetosc w m3 (6 miejsc po przecinku).

        Przyklad: 2972.780000
        """
        return f"{value:.{DECIMAL_PLACES_VOLUME_M3}f}"

    @staticmethod
    def weight_kg(value: float) -> str:
        """Formatuj wage w kg (3 miejsca po przecinku).

        Przyklad: 1500.125
        """
        return f"{value:.{DECIMAL_PLACES_WEIGHT_KG}f}"

    @staticmethod
    def percent(value: float, include_sign: bool = True) -> str:
        """Formatuj procent (2 miejsca po przecinku).

        Przyklad: 12.34% lub 12.34
        """
        formatted = f"{value:.{DECIMAL_PLACES_PERCENT}f}"
        return f"{formatted}%" if include_sign else formatted

    @staticmethod
    def rate(value: float) -> str:
        """Formatuj rate (/hour, /day, /shift) - 3 miejsca po przecinku.

        Przyklad: 4.567
        """
        return f"{value:.{DECIMAL_PLACES_RATE}f}"

    @staticmethod
    def average(value: float) -> str:
        """Formatuj srednia (3 miejsca po przecinku).

        Przyklad: 13.520
        """
        return f"{value:.{DECIMAL_PLACES_AVERAGE}f}"

    @staticmethod
    def ratio(value: float) -> str:
        """Formatuj ratio/CV (3 miejsca po przecinku).

        Przyklad: 0.237
        """
        return f"{value:.{DECIMAL_PLACES_RATIO}f}"

    @staticmethod
    def integer(value: Union[int, float]) -> str:
        """Formatuj liczbe calkowita (bez separatorow tysiecy).

        Przyklad: 22124
        """
        return str(int(value))

    @staticmethod
    def date_iso(value: date) -> str:
        """Formatuj date (YYYY-MM-DD).

        Przyklad: 2025-03-14
        """
        return value.strftime(DATE_FORMAT)

    @staticmethod
    def datetime_iso(value: datetime) -> str:
        """Formatuj datetime (YYYY-MM-DD HH:MM:SS).

        Przyklad: 2025-03-14 08:30:00
        """
        return value.strftime(DATETIME_FORMAT)

    @staticmethod
    def dimension_mm(value: float) -> str:
        """Formatuj wymiar w mm (bez miejsc po przecinku).

        Przyklad: 350
        """
        return str(int(round(value)))

    @staticmethod
    def dimension_m(value: float) -> str:
        """Formatuj wymiar w m (3 miejsca po przecinku).

        Przyklad: 0.350
        """
        return f"{value:.3f}"

    @staticmethod
    def format_value(value: Union[int, float, str, date, datetime, None],
                     value_type: str = "auto") -> str:
        """Uniwersalne formatowanie na podstawie typu.

        Args:
            value: Wartosc do sformatowania
            value_type: Typ formatowania:
                - "volume_m3", "weight_kg", "percent", "rate"
                - "average", "ratio", "integer"
                - "date", "datetime"
                - "auto" - wykryj automatycznie

        Returns:
            Sformatowany string
        """
        if value is None:
            return ""

        if value_type == "auto":
            if isinstance(value, datetime):
                return Formatter.datetime_iso(value)
            elif isinstance(value, date):
                return Formatter.date_iso(value)
            elif isinstance(value, int):
                return Formatter.integer(value)
            elif isinstance(value, float):
                return Formatter.average(value)  # domyslnie 3 miejsca
            else:
                return str(value)

        formatters = {
            "volume_m3": Formatter.volume_m3,
            "weight_kg": Formatter.weight_kg,
            "percent": Formatter.percent,
            "rate": Formatter.rate,
            "average": Formatter.average,
            "ratio": Formatter.ratio,
            "integer": Formatter.integer,
            "date": Formatter.date_iso,
            "datetime": Formatter.datetime_iso,
        }

        formatter = formatters.get(value_type)
        if formatter:
            return formatter(value)

        return str(value)
