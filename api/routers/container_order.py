"""Container Order Calculator router — second Tools tile.

Builds an orderable list of Kardex VBM Box containers (variants + qty) from a
completed analysis. See src/analytics/container_planner.py for the algorithm.
"""

from __future__ import annotations

import io
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.analysis_run import AnalysisRun
from api.models.run_share import RunShare
from api.models.user import User
from api.schemas.container_order import (
    AssignmentRow,
    CatalogResponse,
    ContainerPlanResponse,
    EligibleAnalysis,
    ExportRequest,
    PlanParamsRequest,
    VariantInfo,
    VariantSummaryRow,
)
from src.analytics import container_planner as cp

router = APIRouter(prefix="/api/v1/tools/container-order", tags=["tools-container-order"])


def _has_mib(run: AnalysisRun) -> bool:
    cap = run.capacity_result or {}
    return cp.MIB_CARRIER_ID in (cap.get("carriers_analyzed") or [])


def _abc_counts(run: AnalysisRun) -> dict[str, int]:
    perf = run.performance_result or {}
    out = {"A": 0, "B": 0, "C": 0}
    for row in perf.get("sku_pareto", []) or []:
        cls = row.get("abc_class")
        if cls in out:
            out[cls] += 1
    return out


def _params_to_dataclass(p: PlanParamsRequest) -> cp.PlanParams:
    return cp.PlanParams(
        abc_classes=tuple(p.abc_classes),
        only_machine=p.only_machine,
        include_borderline=p.include_borderline,
        stock_multiplier=p.stock_multiplier,
        location_fill_rate=p.location_fill_rate,
        min_locations_per_sku=p.min_locations_per_sku,
        max_locations_per_sku=p.max_locations_per_sku,
        mode=p.mode,
        auto_max_variants=p.auto_max_variants,
        auto_goal=p.auto_goal,
        guided_preset=p.guided_preset,
        manual_variant_codes=tuple(p.manual_variant_codes),
    )


def _plan_to_response(run: AnalysisRun, plan: cp.ContainerPlan) -> ContainerPlanResponse:
    return ContainerPlanResponse(
        run_id=run.id,
        client_name=run.client_name,
        total_bins=plan.total_bins,
        total_sku_planned=plan.total_sku_planned,
        total_sku_covered=plan.total_sku_covered,
        coverage_pct=plan.coverage_pct,
        avg_fill_pct=plan.avg_fill_pct,
        selected_variant_codes=plan.selected_variant_codes,
        summaries=[VariantSummaryRow(**s.__dict__) for s in plan.summaries],
        assignments=[AssignmentRow(**a.__dict__) for a in plan.assignments],
        orphans=[AssignmentRow(**a.__dict__) for a in plan.orphans],
        params_echo=plan.params_echo,
    )


async def _get_accessible_run(run_id: str, db: AsyncSession, user: User) -> AnalysisRun:
    """Return the run if the user owns it, it's public, or it was shared with them."""
    row = (await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if row.owner_id == user.id or row.is_public:
        return row
    share = (await db.execute(
        select(RunShare).where(RunShare.run_id == run_id, RunShare.shared_with_user_id == user.id)
    )).scalar_one_or_none()
    if share is None:
        raise HTTPException(status_code=403, detail="Access denied")
    return row


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(current_user: User = Depends(get_current_user)) -> CatalogResponse:
    """Return the full 48-variant catalog plus the auto-mode subset codes."""
    return CatalogResponse(
        auto_codes=[v.code for v in cp.CATALOG_AUTO],
        full=[VariantInfo(**v.to_dict()) for v in cp.CATALOG_FULL],
    )


@router.get("/eligible-analyses", response_model=list[EligibleAnalysis])
async def list_eligible_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EligibleAnalysis]:
    """List completed analyses that include the MiB 640x440 carrier."""
    shared_ids_q = select(RunShare.run_id).where(RunShare.shared_with_user_id == current_user.id)
    query = select(AnalysisRun).where(
        (AnalysisRun.owner_id == current_user.id)
        | (AnalysisRun.is_public.is_(True))
        | (AnalysisRun.id.in_(shared_ids_q))
    ).where(AnalysisRun.status.in_(("capacity_done", "performance_done"))) \
     .order_by(AnalysisRun.created_at.desc())
    runs: Iterable[AnalysisRun] = (await db.execute(query)).scalars().all()

    items: list[EligibleAnalysis] = []
    for run in runs:
        if not _has_mib(run):
            continue
        cap = run.capacity_result or {}
        items.append(EligibleAnalysis(
            run_id=run.id,
            client_name=run.client_name,
            status=run.status,
            created_at=run.created_at,
            sku_count=int(cap.get("total_sku") or 0),
            fit_count=int(cap.get("fit_count") or 0),
            fit_pct=float(cap.get("fit_percentage") or 0.0),
            has_performance=bool(run.performance_result),
            abc_distribution=_abc_counts(run),
        ))
    return items


@router.post("/calculate/{run_id}", response_model=ContainerPlanResponse)
async def calculate_plan(
    run_id: str,
    params: PlanParamsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContainerPlanResponse:
    """Compute container plan for the selected run + parameters."""
    run = await _get_accessible_run(run_id, db, current_user)
    if not _has_mib(run):
        raise HTTPException(
            status_code=422,
            detail="This analysis does not include the MiB 640x440 carrier. "
                   "Re-run the capacity analysis with that carrier first.",
        )
    plan = cp.plan_containers(
        run.capacity_result,
        run.performance_result,
        _params_to_dataclass(params),
    )
    return _plan_to_response(run, plan)


@router.post("/export/{run_id}")
async def export_plan(
    run_id: str,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Render the plan as xlsx / pdf / csv. The frontend sends back the plan it last
    calculated so we don't have to recompute server-side."""
    run = await _get_accessible_run(run_id, db, current_user)
    plan = body.plan

    safe_client = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in run.client_name) or "analysis"
    filename = f"container_order_{safe_client}_{run_id[:8]}.{body.format}"

    if body.format == "xlsx":
        from api.excel_generator import generate_order_xlsx
        data = generate_order_xlsx(plan, body.params, run)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif body.format == "pdf":
        from api.pdf_generator import generate_container_order_pdf
        data = generate_container_order_pdf(plan, body.params, run)
        media = "application/pdf"
    elif body.format == "csv":
        data = _generate_summary_csv(plan)
        media = "text/csv"
    else:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {body.format}")

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _generate_summary_csv(plan: ContainerPlanResponse) -> bytes:
    """One-sheet summary CSV — same columns as Sheet 1 in the xlsx."""
    buf = io.StringIO()
    buf.write("variant_code;footprint;bin_height_mm;cell_LxWxH_mm;locations_per_bin;sku_count;total_locations;bins_required;avg_fill_pct\n")
    for s in plan.summaries:
        cell = f"{s.cell_length_mm}x{s.cell_width_mm}x{s.cell_height_mm}"
        buf.write(
            f"{s.code};{s.footprint_label};{s.bin_height_mm};{cell};{s.locations_per_bin};"
            f"{s.sku_count};{s.total_locations};{s.bins_required};{s.avg_fill_pct}\n"
        )
    buf.write(f"\nTOTAL;;;;;{plan.total_sku_covered};;{plan.total_bins};{plan.avg_fill_pct}\n")
    return buf.getvalue().encode("utf-8-sig")
