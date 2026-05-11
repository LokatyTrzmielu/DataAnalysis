"""Orders data validation — basic stats, gaps, anomalies, cross-validation."""

from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

import polars as pl

from src.ingest.cleaning import clean_numeric_column


_PLACEHOLDER_SKUS = {
    "", "n/a", "na", "-", "0", "null", "none", "unknown", "undefined", "?",
}


class OrdersValidator:
    """Validates an ingested orders DataFrame and returns a plain dict."""

    def validate(
        self,
        df: pl.DataFrame,
        masterdata_path: Optional[Path] = None,
        masterdata_mapping: Optional[dict] = None,
        masterdata_df: Optional[pl.DataFrame] = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result.update(self._summary_kpis(df))
        result.update(self._check_missing_skus(df))
        result.update(self._check_date_gaps(df))
        result.update(self._check_quantity_anomalies(df))
        result.update(self._check_sku_crossvalidation(df, masterdata_path, masterdata_mapping, masterdata_df))
        result.update(self._compute_weekday_profile(df))
        return result

    # ── Summary KPIs ─────────────────────────────────────────────────────────

    def _summary_kpis(self, df: pl.DataFrame) -> dict[str, Any]:
        total_rows = len(df)

        date_from: Optional[str] = None
        date_to: Optional[str] = None
        unique_days = 0
        has_hourly_data = False

        if "order_date" in df.columns:
            dates = df["order_date"].drop_nulls()
            unique_days = dates.n_unique()
            if unique_days > 0:
                date_from = str(dates.min())
                date_to = str(dates.max())

        if "order_hour" in df.columns:
            has_hourly_data = df.filter(pl.col("order_hour") != 0).height > 0

        return {
            "total_rows": total_rows,
            "date_from": date_from,
            "date_to": date_to,
            "unique_days": unique_days,
            "has_hourly_data": has_hourly_data,
        }

    # ── Missing SKUs ──────────────────────────────────────────────────────────

    def _check_missing_skus(self, df: pl.DataFrame) -> dict[str, Any]:
        total = len(df)
        if "sku" not in df.columns or total == 0:
            return {"missing_sku_count": 0, "missing_sku_pct": 0.0}

        def _is_missing(val: Any) -> bool:
            if val is None:
                return True
            return str(val).strip().lower() in _PLACEHOLDER_SKUS

        missing = df.filter(
            pl.col("sku").is_null()
            | pl.col("sku").cast(pl.Utf8).str.strip_chars().str.to_lowercase().is_in(list(_PLACEHOLDER_SKUS))
        ).height

        return {
            "missing_sku_count": missing,
            "missing_sku_pct": round(missing / total * 100, 2) if total > 0 else 0.0,
        }

    # ── Date gaps ─────────────────────────────────────────────────────────────

    def _check_date_gaps(self, df: pl.DataFrame) -> dict[str, Any]:
        empty = {
            "date_coverage_pct": 0.0,
            "total_calendar_days": 0,
            "gap_count": 0,
            "max_gap_days": 0,
            "gap_list": [],
        }

        if "order_date" not in df.columns:
            return empty

        dates_col = df["order_date"].drop_nulls()
        if dates_col.is_empty():
            return empty

        d_min: date = dates_col.min()  # type: ignore[assignment]
        d_max: date = dates_col.max()  # type: ignore[assignment]
        total_calendar = (d_max - d_min).days + 1

        active_dates: set[date] = set(dates_col.to_list())
        full_range = {d_min + timedelta(days=i) for i in range(total_calendar)}
        gap_dates = sorted(full_range - active_dates)

        coverage_pct = round(len(active_dates) / total_calendar * 100, 2) if total_calendar > 0 else 0.0

        # Build consecutive gap intervals
        gap_intervals: list[dict[str, Any]] = []
        if gap_dates:
            start = gap_dates[0]
            end = gap_dates[0]
            for gd in gap_dates[1:]:
                if (gd - end).days == 1:
                    end = gd
                else:
                    gap_intervals.append({
                        "from": str(start),
                        "to": str(end),
                        "days": (end - start).days + 1,
                    })
                    start = gd
                    end = gd
            gap_intervals.append({
                "from": str(start),
                "to": str(end),
                "days": (end - start).days + 1,
            })

        gap_intervals.sort(key=lambda g: g["days"], reverse=True)
        max_gap = gap_intervals[0]["days"] if gap_intervals else 0

        return {
            "date_coverage_pct": coverage_pct,
            "total_calendar_days": total_calendar,
            "gap_count": len(gap_intervals),
            "max_gap_days": max_gap,
            "gap_list": gap_intervals[:20],
        }

    # ── Quantity anomalies ────────────────────────────────────────────────────

    def _check_quantity_anomalies(self, df: pl.DataFrame) -> dict[str, Any]:
        empty = {
            "qty_null_count": 0,
            "qty_zero_count": 0,
            "qty_negative_count": 0,
            "qty_outlier_count": 0,
            "qty_outlier_threshold": 0.0,
        }

        if "quantity" not in df.columns:
            return empty

        # Handles both already-numeric columns and Utf8 with European format ("1,5" → 1.5)
        qty = df.with_columns(
            clean_numeric_column(pl.col("quantity")).alias("__qty__")
        )["__qty__"]
        qty_null = qty.is_null().sum()
        qty_zero = qty.filter(qty.eq(0)).len() if qty.drop_nulls().len() > 0 else 0
        qty_negative = qty.filter(qty.lt(0)).len() if qty.drop_nulls().len() > 0 else 0

        # Outliers: values > mean + 3σ among positive values
        positive = qty.drop_nulls().filter(qty.drop_nulls().gt(0))
        outlier_count = 0
        outlier_threshold = 0.0
        if positive.len() > 3:
            mean_val = float(positive.mean() or 0)
            std_val = float(positive.std() or 0)
            if std_val > 0:
                outlier_threshold = round(mean_val + 3 * std_val, 2)
                outlier_count = positive.filter(positive.gt(outlier_threshold)).len()

        return {
            "qty_null_count": int(qty_null or 0),
            "qty_zero_count": int(qty_zero or 0),
            "qty_negative_count": int(qty_negative or 0),
            "qty_outlier_count": int(outlier_count or 0),
            "qty_outlier_threshold": outlier_threshold,
        }

    # ── SKU cross-validation ──────────────────────────────────────────────────

    def _check_sku_crossvalidation(
        self,
        df: pl.DataFrame,
        masterdata_path: Optional[Path],
        masterdata_mapping: Optional[dict],
        masterdata_df: Optional[pl.DataFrame] = None,
    ) -> dict[str, Any]:
        unavailable = {
            "sku_xval_available": False,
            "orders_skus_not_in_masterdata_count": 0,
            "orders_skus_not_in_masterdata": [],
            "masterdata_skus_not_in_orders_count": 0,
            "masterdata_skus_not_in_orders": [],
        }

        if "sku" not in df.columns:
            return unavailable

        try:
            if masterdata_df is not None:
                loaded_df = masterdata_df
            elif masterdata_path and masterdata_path.exists():
                from src.ingest.pipeline import MasterdataIngestPipeline
                from src.ingest.mapping import MappingResult, ColumnMapping

                pipeline = MasterdataIngestPipeline()

                if masterdata_mapping:
                    mappings = {
                        k: ColumnMapping(target_field=k, source_column=v, confidence=1.0, is_auto=False)
                        for k, v in masterdata_mapping.items()
                        if v
                    }
                    mapping = MappingResult(mappings=mappings, missing_required=[])
                    loaded_df = pipeline.run(masterdata_path, mapping=mapping).df
                else:
                    loaded_df = pipeline.run(masterdata_path).df
            else:
                return unavailable

            if "sku" not in loaded_df.columns:
                return unavailable

            md_skus: set[str] = set(loaded_df["sku"].drop_nulls().to_list())
            orders_skus: set[str] = set(df["sku"].drop_nulls().cast(pl.Utf8).to_list())

            # Remove placeholder SKUs from orders set
            orders_skus = {s for s in orders_skus if s.strip().lower() not in _PLACEHOLDER_SKUS}

            not_in_md = sorted(orders_skus - md_skus)
            not_in_orders = sorted(md_skus - orders_skus)

            return {
                "sku_xval_available": True,
                "orders_skus_not_in_masterdata_count": len(not_in_md),
                "orders_skus_not_in_masterdata": not_in_md[:100],
                "masterdata_skus_not_in_orders_count": len(not_in_orders),
                "masterdata_skus_not_in_orders": not_in_orders[:100],
            }
        except Exception:
            return unavailable

    # ── Working pattern profile ───────────────────────────────────────────────

    def _compute_weekday_profile(self, df: pl.DataFrame) -> dict[str, Any]:
        empty = {
            "weekday_distribution": {},
            "most_active_weekday": None,
            "least_active_weekday": None,
        }

        if "order_date" not in df.columns or len(df) == 0:
            return empty

        total = len(df)
        wd_df = df.with_columns([
            # Polars dt.weekday() returns 1=Mon..7=Sun; convert to 0-based
            (pl.col("order_date").cast(pl.Date).dt.weekday() - 1).alias("_wd")
        ]).group_by("_wd").agg(pl.len().alias("cnt")).sort("_wd")

        distribution: dict[str, float] = {}
        for row in wd_df.to_dicts():
            wd = row["_wd"]
            if wd is not None and 0 <= wd <= 6:
                distribution[str(wd)] = round(row["cnt"] / total * 100, 2)

        if not distribution:
            return empty

        most_active = max(distribution, key=lambda k: distribution[k])
        least_active = min(distribution, key=lambda k: distribution[k])

        return {
            "weekday_distribution": distribution,
            "most_active_weekday": int(most_active),
            "least_active_weekday": int(least_active),
        }
