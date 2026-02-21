"""Pydantic schemas for analysis API responses."""

from dataclasses import asdict
from typing import Any, Optional

from pydantic import BaseModel

from src.analytics.capacity import CapacityAnalysisResult, CarrierStats


class CarrierStatsResponse(BaseModel):
    carrier_id: str
    carrier_name: str
    fit_count: int
    borderline_count: int
    not_fit_count: int
    fit_percentage: float
    total_volume_m3: float
    stock_volume_m3: float
    total_locations_required: int
    avg_filling_rate: float


class CapacityResponse(BaseModel):
    total_sku: int
    fit_count: int
    borderline_count: int
    not_fit_count: int
    fit_percentage: float
    carriers_analyzed: list[str]
    carrier_stats: dict[str, CarrierStatsResponse]
    rows: list[dict[str, Any]]

    @classmethod
    def from_result(cls, result: CapacityAnalysisResult) -> "CapacityResponse":
        """Build response from CapacityAnalysisResult."""
        carrier_stats_resp = {
            cid: CarrierStatsResponse(**asdict(cs))
            for cid, cs in result.carrier_stats.items()
        }
        # Polars DataFrame → list of dicts (None values kept as-is)
        rows = result.df.to_dicts()
        return cls(
            total_sku=result.total_sku,
            fit_count=result.fit_count,
            borderline_count=result.borderline_count,
            not_fit_count=result.not_fit_count,
            fit_percentage=result.fit_percentage,
            carriers_analyzed=result.carriers_analyzed,
            carrier_stats=carrier_stats_resp,
            rows=rows,
        )
