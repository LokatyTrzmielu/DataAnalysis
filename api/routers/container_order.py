"""Container Order Calculator router — second Tools tile.

Builds an orderable list of Kardex VBM Box containers (variants + qty) from a
completed analysis. See src/analytics/container_planner.py for the algorithm.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.analysis_run import AnalysisRun
from api.models.container_order_plan import ContainerOrderPlan
from api.models.run_share import RunShare
from api.models.user import User
from api.services.time_saving import record_event as record_time_saving_event
from api.schemas.container_order import (
    AssignmentRow,
    CatalogResponse,
    ContainerPlanResponse,
    EligibleAnalysis,
    ExportRequest,
    PlanParamsRequest,
    SavedPlanCreate,
    SavedPlanDetail,
    SavedPlanListResponse,
    SavedPlanPatch,
    SavedPlanResponse,
    VariantInfo,
    VariantSummaryRow,
)
from src.analytics import container_planner as cp

router = APIRouter(prefix="/api/v1/tools/container-order", tags=["tools-container-order"])


def _has_mib(run: AnalysisRun) -> bool:
    cap = run.capacity_result or {}
    return cp.MIB_CARRIER_ID in (cap.get("carriers_analyzed") or [])


def _mib_stats(run: AnalysisRun) -> tuple[int, int, int, float]:
    """Return (fit, borderline, not_fit, fit_pct) for the MiB carrier.

    Falls back to zeros for older runs that don't carry per-carrier stats.
    """
    cap = run.capacity_result or {}
    stats = (cap.get("carrier_stats") or {}).get(cp.MIB_CARRIER_ID) or {}
    return (
        int(stats.get("fit_count") or 0),
        int(stats.get("borderline_count") or 0),
        int(stats.get("not_fit_count") or 0),
        float(stats.get("fit_percentage") or 0.0),
    )


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
        impute_missing_dimensions=p.impute_missing_dimensions,
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
        total_frames=plan.total_frames,
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
        mib_fit, mib_borderline, mib_not_fit, mib_pct = _mib_stats(run)
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
            mib_fit_count=mib_fit,
            mib_borderline_count=mib_borderline,
            mib_not_fit_count=mib_not_fit,
            mib_fit_pct=mib_pct,
            mib_planned_sku=mib_fit + mib_borderline,
            carriers_analyzed=list(cap.get("carriers_analyzed") or []),
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
    await record_time_saving_event(
        db,
        current_user.id,
        "container_order_run",
        run_id=run.id,
        sku_count=plan.total_sku_planned,
        variant_count=len(plan.summaries),
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
        data = generate_order_xlsx(plan, body.params, run, current_user)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        sheet_count = 4   # Order Summary, SKU Assignment, Parameters, Orphans
    elif body.format == "pdf":
        from api.pdf_generator import generate_container_order_pdf
        data = generate_container_order_pdf(plan, body.params, run, current_user)
        media = "application/pdf"
        sheet_count = 2   # KPI+chart+table page, parameters page
    elif body.format == "csv":
        data = _generate_summary_csv(plan)
        media = "text/csv"
        sheet_count = 1
    else:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {body.format}")

    await record_time_saving_event(
        db,
        current_user.id,
        "container_order_exported",
        run_id=run.id,
        sheet_count=sheet_count,
    )

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _generate_summary_csv(plan: ContainerPlanResponse) -> bytes:
    """One-sheet summary CSV — same columns as Sheet 1 in the xlsx, including
    the Bases / Frames / Dividers procurement breakdown."""
    buf = io.StringIO()
    buf.write(
        "variant_code;footprint;bin_height_mm;cell_LxWxH_mm;locations_per_bin;"
        "sku_count;total_locations;bins_required;bases;frames;dividers;"
        "total_weight_kg;avg_fill_pct\n"
    )
    total_dividers = 0
    total_weight = 0.0
    for s in plan.summaries:
        cell = f"{s.cell_length_mm}x{s.cell_width_mm}x{s.cell_height_mm}"
        total_dividers += s.dividers_required
        total_weight += s.total_weight_kg
        buf.write(
            f"{s.code};{s.footprint_label};{s.bin_height_mm};{cell};{s.locations_per_bin};"
            f"{s.sku_count};{s.total_locations};{s.bins_required};"
            f"{s.bins_required};{s.total_frames_required};{s.dividers_required};"
            f"{s.total_weight_kg:.2f};{s.avg_fill_pct}\n"
        )
    buf.write(
        f"\nTOTAL;;;;;{plan.total_sku_covered};;{plan.total_bins};"
        f"{plan.total_bins};{plan.total_frames};{total_dividers};"
        f"{total_weight:.2f};{plan.avg_fill_pct}\n"
    )
    return buf.getvalue().encode("utf-8-sig")


# ── Saved plans (history) ──────────────────────────────────────────────────


async def _get_owned_saved_plan(plan_id: str, db: AsyncSession, user: User) -> ContainerOrderPlan:
    """Owner-only access for v1 (no sharing yet). 404 if missing, 403 if not owner."""
    row = (await db.execute(
        select(ContainerOrderPlan).where(ContainerOrderPlan.id == plan_id)
    )).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Saved plan not found")
    if row.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return row


async def _existing_run_ids(db: AsyncSession, run_ids: Iterable[str]) -> set[str]:
    """Return the subset of run_ids that still exist in analysis_runs."""
    ids = [rid for rid in run_ids if rid]
    if not ids:
        return set()
    rows = (await db.execute(
        select(AnalysisRun.id).where(AnalysisRun.id.in_(ids))
    )).scalars().all()
    return set(rows)


def _saved_plan_response(p: ContainerOrderPlan, source_run_available: bool) -> SavedPlanResponse:
    plan_snapshot = p.plan or {}
    params_snapshot = p.params or {}
    return SavedPlanResponse(
        id=p.id,
        label=p.label,
        client_name=p.client_name,
        source_run_id=p.source_run_id,
        source_run_available=source_run_available,
        created_at=p.created_at,
        updated_at=p.updated_at,
        total_bins=int(plan_snapshot.get("total_bins") or 0),
        total_frames=int(plan_snapshot.get("total_frames") or 0),
        total_sku_covered=int(plan_snapshot.get("total_sku_covered") or 0),
        coverage_pct=float(plan_snapshot.get("coverage_pct") or 0.0),
        mode=str(params_snapshot.get("mode") or ""),
        notes=p.notes,
    )


@router.post("/plans", response_model=SavedPlanResponse, status_code=201)
async def save_plan(
    body: SavedPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedPlanResponse:
    """Save the current computed plan to the user's history.

    The frontend ships back the full PlanParamsRequest + ContainerPlanResponse
    it has in store, so the server doesn't recompute. Snapshots are immutable
    against later changes to the source AnalysisRun.
    """
    run = await _get_accessible_run(body.run_id, db, current_user)
    default_label = f"{run.client_name} — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    label = (body.label or "").strip() or default_label

    saved = ContainerOrderPlan(
        owner_id=current_user.id,
        source_run_id=run.id,
        label=label,
        client_name=run.client_name,
        params=body.params.model_dump(),
        plan=body.plan.model_dump(),
        notes=(body.notes or None),
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return _saved_plan_response(saved, source_run_available=True)


@router.get("/plans", response_model=SavedPlanListResponse)
async def list_saved_plans(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedPlanListResponse:
    """Paginated history list for the current user, newest first."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    base = select(ContainerOrderPlan).where(ContainerOrderPlan.owner_id == current_user.id)
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    rows: list[ContainerOrderPlan] = (await db.execute(
        base.order_by(ContainerOrderPlan.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    alive = await _existing_run_ids(db, [r.source_run_id for r in rows if r.source_run_id])
    items = [
        _saved_plan_response(r, source_run_available=(r.source_run_id in alive))
        for r in rows
    ]
    return SavedPlanListResponse(items=items, total=int(total))


@router.get("/plans/{plan_id}", response_model=SavedPlanDetail)
async def get_saved_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedPlanDetail:
    """Full snapshot — used to restore the Calculation tab from history."""
    row = await _get_owned_saved_plan(plan_id, db, current_user)
    alive = await _existing_run_ids(db, [row.source_run_id] if row.source_run_id else [])
    base = _saved_plan_response(row, source_run_available=(row.source_run_id in alive))
    return SavedPlanDetail(
        **base.model_dump(),
        params=PlanParamsRequest(**(row.params or {})),
        plan=ContainerPlanResponse(**(row.plan or {})),
    )


@router.patch("/plans/{plan_id}", response_model=SavedPlanResponse)
async def patch_saved_plan(
    plan_id: str,
    body: SavedPlanPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedPlanResponse:
    """Rename or update notes on a saved plan. Owner only."""
    row = await _get_owned_saved_plan(plan_id, db, current_user)
    if body.label is not None:
        label = body.label.strip()
        if label:
            row.label = label
    if body.notes is not None:
        row.notes = body.notes.strip() or None
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    alive = await _existing_run_ids(db, [row.source_run_id] if row.source_run_id else [])
    return _saved_plan_response(row, source_run_available=(row.source_run_id in alive))


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_saved_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    row = await _get_owned_saved_plan(plan_id, db, current_user)
    await db.delete(row)
    await db.commit()
    return Response(status_code=204)
