"""Carriers CRUD router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.carrier import Carrier
from api.models.user import User
from api.schemas.carriers import CarrierCreate, CarrierResponse, CarrierUpdate

router = APIRouter(prefix="/api/v1/carriers", tags=["carriers"])


def _to_response(c: Carrier) -> CarrierResponse:
    return CarrierResponse(
        id=c.id,
        carrier_id=c.carrier_id,
        name=c.name,
        inner_length_mm=c.inner_length_mm,
        inner_width_mm=c.inner_width_mm,
        inner_height_mm=c.inner_height_mm,
        max_weight_kg=c.max_weight_kg,
        is_predefined=c.is_predefined,
        is_active=c.is_active,
        priority=c.priority,
    )


@router.get("", response_model=list[CarrierResponse])
async def list_carriers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CarrierResponse]:
    result = await db.execute(select(Carrier).order_by(Carrier.priority.nullslast(), Carrier.name))
    return [_to_response(c) for c in result.scalars().all()]


@router.post("", response_model=CarrierResponse, status_code=status.HTTP_201_CREATED)
async def create_carrier(
    body: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CarrierResponse:
    existing = await db.execute(
        select(Carrier).where(Carrier.carrier_id == body.carrier_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Carrier '{body.carrier_id}' already exists"
        )
    carrier = Carrier(**body.model_dump(), is_predefined=False)
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    return _to_response(carrier)


@router.patch("/{carrier_id}", response_model=CarrierResponse)
async def update_carrier(
    carrier_id: str,
    body: CarrierUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CarrierResponse:
    result = await db.execute(
        select(Carrier).where(Carrier.carrier_id == carrier_id)
    )
    carrier = result.scalar_one_or_none()
    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(carrier, field, value)

    await db.commit()
    await db.refresh(carrier)
    return _to_response(carrier)


@router.delete("/{carrier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carrier(
    carrier_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(Carrier).where(Carrier.carrier_id == carrier_id)
    )
    carrier = result.scalar_one_or_none()
    if carrier is None:
        raise HTTPException(status_code=404, detail="Carrier not found")
    if carrier.is_predefined:
        raise HTTPException(status_code=403, detail="Cannot delete predefined carrier")
    await db.delete(carrier)
    await db.commit()
