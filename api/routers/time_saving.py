"""Time-saving counter — exposes the per-user summary used in Settings."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db
from api.models.user import User
from api.services.time_saving import get_summary_for_user

router = APIRouter(prefix="/api/v1/users/me", tags=["time-savings"])


class TimeSavingBreakdownResponse(BaseModel):
    event_type: str
    label: str
    count: int
    seconds: int


class TimeSavingSummaryResponse(BaseModel):
    total_seconds: int
    total_events: int
    breakdown: list[TimeSavingBreakdownResponse]


@router.get("/time-savings", response_model=TimeSavingSummaryResponse)
async def my_time_savings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeSavingSummaryResponse:
    """Return total minutes saved + per-event-type breakdown for the current user."""
    summary = await get_summary_for_user(db, current_user.id)
    return TimeSavingSummaryResponse(
        total_seconds=summary.total_seconds,
        total_events=summary.total_events,
        breakdown=[
            TimeSavingBreakdownResponse(
                event_type=b.event_type,
                label=b.label,
                count=b.count,
                seconds=b.seconds,
            )
            for b in summary.breakdown
        ],
    )
