"""Excel (xlsx) generator for the Container Order Calculator tool."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill(start_color="374151", end_color="374151", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TOTAL_FILL = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid")
TOTAL_FONT = Font(bold=True, size=11)
CENTER = Alignment(horizontal="center", vertical="center")
RIGHT = Alignment(horizontal="right", vertical="center")


def _style_header(ws, row: int, n_cols: int) -> None:
    for col in range(1, n_cols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
    ws.row_dimensions[row].height = 22
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def _autosize(ws) -> None:
    for col_idx, col in enumerate(ws.columns, start=1):
        max_len = 0
        for cell in col:
            v = cell.value
            if v is not None:
                max_len = max(max_len, len(str(v)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 48)


def _sheet_order_summary(wb: Workbook, plan: Any) -> None:
    ws = wb.create_sheet("Order Summary", 0)
    headers = ["Variant", "Footprint", "Bin height (mm)", "Cell L×W×H (mm)",
               "Locations / bin", "SKU count", "Locations total", "Bins to order",
               "Avg cell fill (%)"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for s in plan.summaries:
        cell = f"{s.cell_length_mm}×{s.cell_width_mm}×{s.cell_height_mm}"
        ws.append([
            s.code, s.footprint_label, s.bin_height_mm, cell,
            s.locations_per_bin, s.sku_count, s.total_locations,
            s.bins_required, s.avg_fill_pct,
        ])

    # TOTAL row
    total_row = ws.max_row + 1
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=6, value=plan.total_sku_covered)
    ws.cell(row=total_row, column=8, value=plan.total_bins)
    ws.cell(row=total_row, column=9, value=plan.avg_fill_pct)
    for col in range(1, len(headers) + 1):
        c = ws.cell(row=total_row, column=col)
        c.fill = TOTAL_FILL
        c.font = TOTAL_FONT

    _autosize(ws)


def _sheet_sku_assignment(wb: Workbook, plan: Any) -> None:
    ws = wb.create_sheet("SKU Assignment")
    headers = ["SKU", "Variant", "ABC", "Recommendation", "Length (mm)", "Width (mm)",
               "Height (mm)", "Weight (kg)", "Stock vol (L)", "Locations", "Bins",
               "Cell fill (%)"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for a in plan.assignments:
        ws.append([
            a.sku, a.variant_code or "—", a.abc_class or "", a.recommendation or "",
            a.length_mm, a.width_mm, a.height_mm, a.weight_kg, a.stock_volume_L,
            a.locations, a.bins, a.cell_fill_pct,
        ])
    _autosize(ws)


def _sheet_parameters(wb: Workbook, params: Any, run: Any, plan: Any) -> None:
    ws = wb.create_sheet("Parameters")
    ws.append(["Parameter", "Value"])
    _style_header(ws, 1, 2)

    pairs = [
        ("Run ID", run.id),
        ("Client", run.client_name),
        ("Generated at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Mode", params.mode),
        ("Auto: goal", params.auto_goal if params.mode == "auto" else "—"),
        ("Auto: max variants", params.auto_max_variants if params.mode == "auto" else "—"),
        ("Guided: preset", params.guided_preset if params.mode == "guided" else "—"),
        ("Manual: variant codes", ", ".join(params.manual_variant_codes) if params.mode == "manual" else "—"),
        ("ABC classes", ", ".join(params.abc_classes) if params.abc_classes else "all"),
        ("Only Machine SKUs", "Yes" if params.only_machine else "No"),
        ("Include BORDERLINE", "Yes" if params.include_borderline else "No"),
        ("Stock multiplier", f"{params.stock_multiplier:.2f}"),
        ("Location fill rate", f"{params.location_fill_rate * 100:.0f}%"),
        ("Min locations / SKU", params.min_locations_per_sku),
        ("Max locations / SKU", params.max_locations_per_sku),
        ("", ""),
        ("Total bins to order", plan.total_bins),
        ("SKUs covered", f"{plan.total_sku_covered} of {plan.total_sku_planned} ({plan.coverage_pct:.1f}%)"),
        ("Average cell fill", f"{plan.avg_fill_pct:.1f}%"),
    ]
    for k, v in pairs:
        ws.append([k, v])
    _autosize(ws)


def _sheet_orphans(wb: Workbook, plan: Any) -> None:
    ws = wb.create_sheet("Orphans")
    headers = ["SKU", "ABC", "Recommendation", "Length (mm)", "Width (mm)",
               "Height (mm)", "Weight (kg)", "Stock vol (L)", "Reason"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for a in plan.orphans:
        reason = "No variant in selection fits this SKU"
        ws.append([
            a.sku, a.abc_class or "", a.recommendation or "",
            a.length_mm, a.width_mm, a.height_mm, a.weight_kg, a.stock_volume_L,
            reason,
        ])
    if not plan.orphans:
        ws.append(["(no orphan SKUs)", "", "", "", "", "", "", "", ""])
    _autosize(ws)


def generate_order_xlsx(plan: Any, params: Any, run: Any) -> bytes:
    """Build the 4-sheet workbook. `plan` is ContainerPlanResponse, `params` is
    PlanParamsRequest, `run` is the SQLAlchemy AnalysisRun."""
    wb = Workbook()
    # openpyxl creates a default sheet — remove it (we'll add named sheets ourselves).
    default = wb.active
    if default is not None and default.title == "Sheet":
        wb.remove(default)

    _sheet_order_summary(wb, plan)
    _sheet_sku_assignment(wb, plan)
    _sheet_parameters(wb, params, run, plan)
    _sheet_orphans(wb, plan)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
