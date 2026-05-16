"""Unit + integration tests for the time-saving accounting feature."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.database import Base
from api.dependencies import get_db
from api.main import app
from api.models.time_saving_event import TimeSavingEvent
from api.services.time_saving import (
    EVENT_LABELS,
    TIME_SAVING_RULES,
    calculate_manual_seconds,
    get_summary_for_user,
    record_event,
)


# ---------------------------------------------------------------------------
# Unit tests — calculate_manual_seconds (pure function)
# ---------------------------------------------------------------------------

class TestCalculateManualSeconds:
    def test_unknown_event_returns_zero(self):
        assert calculate_manual_seconds("nonsense_event") == 0

    def test_base_only_no_scale(self):
        # Quality with 0 rows -> just base
        assert calculate_manual_seconds("quality_run") == TIME_SAVING_RULES["quality_run"]["base_seconds"]

    def test_masterdata_scales_with_rows(self):
        # 3000 rows = 15min base + 3 * 5min = 30min = 1800s
        assert calculate_manual_seconds("dataset_imported_masterdata", row_count=3000) == 1800

    def test_orders_scales_with_rows(self):
        # 50000 rows = 20min base + 50 * 4min = 220min = 13200s
        assert calculate_manual_seconds("dataset_imported_orders", row_count=50000) == 13200

    def test_capacity_scales_with_sku_and_carriers(self):
        # 3000 sku x 5 carriers = 45min base + 30min sku + 25min carriers = 100min = 6000s
        assert calculate_manual_seconds("capacity_run", sku_count=3000, carrier_count=5) == 6000

    def test_capacity_no_scale_still_returns_base(self):
        assert calculate_manual_seconds("capacity_run") == TIME_SAVING_RULES["capacity_run"]["base_seconds"]

    def test_performance_with_pareto(self):
        # 50k lines + pareto = 40min base + (50 * 1min) + 25min = 115min
        assert calculate_manual_seconds(
            "performance_run", lines_count=50000, includes_pareto=True
        ) == 115 * 60

    def test_performance_without_pareto_skips_bonus(self):
        # 50k lines no pareto = 40 + 50 = 90 min
        assert calculate_manual_seconds("performance_run", lines_count=50000) == 90 * 60

    def test_performance_caps_huge_datasets(self):
        # 1M lines + pareto would raw = 40 + 1000 + 25 = 1065min ~ 17h,
        # but max_seconds caps it at 6h.
        seconds = calculate_manual_seconds(
            "performance_run", lines_count=1_000_000, includes_pareto=True
        )
        assert seconds == 6 * 3600

    def test_pdf_scales_with_charts(self):
        # 5 charts = 45min base + 25min = 70min = 4200s
        assert calculate_manual_seconds("report_exported_pdf", chart_count=5) == 4200

    def test_zip_scales_with_csvs(self):
        # 8 csv = 25min base + 16min = 41min = 2460s
        assert calculate_manual_seconds("report_exported_zip", csv_count=8) == 2460

    def test_zero_scale_treated_as_no_scale(self):
        assert calculate_manual_seconds("dataset_imported_masterdata", row_count=0) == 15 * 60

    def test_none_scale_treated_as_no_scale(self):
        assert calculate_manual_seconds("dataset_imported_masterdata", row_count=None) == 15 * 60

    def test_every_event_type_has_a_label(self):
        for event_type in TIME_SAVING_RULES:
            assert event_type in EVENT_LABELS, f"missing label for {event_type}"


# ---------------------------------------------------------------------------
# Integration — DB persistence + summary aggregation
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    await engine.dispose()


class TestRecordAndSummary:
    @pytest.mark.asyncio
    async def test_record_event_persists_row(self, db_session):
        event = await record_event(
            db_session,
            "user-1",
            "capacity_run",
            run_id="run-1",
            sku_count=2000,
            carrier_count=3,
        )
        assert event is not None
        assert event.user_id == "user-1"
        assert event.manual_seconds > 0
        assert event.scale_value == 2000
        # 45min + 20min + 15min = 80min
        assert event.manual_seconds == 80 * 60

    @pytest.mark.asyncio
    async def test_summary_isolates_per_user(self, db_session):
        await record_event(db_session, "alice", "capacity_run", sku_count=1000, carrier_count=2)
        await record_event(db_session, "alice", "quality_run", row_count=1000)
        await record_event(db_session, "bob", "capacity_run", sku_count=1000, carrier_count=2)

        alice_summary = await get_summary_for_user(db_session, "alice")
        bob_summary = await get_summary_for_user(db_session, "bob")

        assert alice_summary.total_events == 2
        assert bob_summary.total_events == 1
        # Alice's total should include both events; Bob's only one capacity.
        assert alice_summary.total_seconds > bob_summary.total_seconds

        alice_types = {b.event_type for b in alice_summary.breakdown}
        assert alice_types == {"capacity_run", "quality_run"}

    @pytest.mark.asyncio
    async def test_summary_empty_user_returns_zeros(self, db_session):
        summary = await get_summary_for_user(db_session, "nobody")
        assert summary.total_seconds == 0
        assert summary.total_events == 0
        assert summary.breakdown == []

    @pytest.mark.asyncio
    async def test_breakdown_sorted_by_seconds_desc(self, db_session):
        # quality_run gets larger row_count so it should outrank capacity
        await record_event(db_session, "u1", "capacity_run", sku_count=500, carrier_count=1)
        await record_event(db_session, "u1", "quality_run", row_count=100000)

        summary = await get_summary_for_user(db_session, "u1")
        assert len(summary.breakdown) == 2
        assert summary.breakdown[0].seconds >= summary.breakdown[1].seconds


# ---------------------------------------------------------------------------
# Endpoint test — auth + isolation per user
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def shared_engine_client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, factory

    app.dependency_overrides.clear()
    await engine.dispose()


async def _seed_user(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/users",
        json={"email": email, "name": email.split("@")[0], "password": "pw123456"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pw123456"},
    )
    return resp.json()["access_token"]


class TestEndpoint:
    @pytest.mark.asyncio
    async def test_unauthorized_without_token(self, shared_engine_client):
        client, _ = shared_engine_client
        resp = await client.get("/api/v1/users/me/time-savings")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_summary_for_new_user(self, shared_engine_client):
        client, _ = shared_engine_client
        token = await _seed_user(client, "alice@test.com")
        resp = await client.get(
            "/api/v1/users/me/time-savings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_seconds"] == 0
        assert data["total_events"] == 0
        assert data["breakdown"] == []

    @pytest.mark.asyncio
    async def test_endpoint_returns_seeded_events(self, shared_engine_client):
        client, factory = shared_engine_client
        token = await _seed_user(client, "alice@test.com")

        # Look up alice's id
        async with factory() as db:
            from api.models.user import User as UserModel
            alice = (await db.execute(
                select(UserModel).where(UserModel.email == "alice@test.com")
            )).scalar_one()

            await record_event(db, alice.id, "capacity_run", sku_count=1000, carrier_count=2)
            await record_event(db, alice.id, "quality_run", row_count=5000)

        resp = await client.get(
            "/api/v1/users/me/time-savings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 2
        assert data["total_seconds"] > 0
        labels = {row["label"] for row in data["breakdown"]}
        assert "Capacity analysis" in labels
        assert "Quality (DQ) analysis" in labels

    @pytest.mark.asyncio
    async def test_endpoint_isolates_users(self, shared_engine_client):
        client, factory = shared_engine_client
        alice_token = await _seed_user(client, "alice@test.com")
        bob_token = await _seed_user(client, "bob@test.com")

        async with factory() as db:
            from api.models.user import User as UserModel
            alice = (await db.execute(
                select(UserModel).where(UserModel.email == "alice@test.com")
            )).scalar_one()
            await record_event(db, alice.id, "capacity_run", sku_count=1000, carrier_count=2)

        alice_resp = await client.get(
            "/api/v1/users/me/time-savings",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        bob_resp = await client.get(
            "/api/v1/users/me/time-savings",
            headers={"Authorization": f"Bearer {bob_token}"},
        )
        assert alice_resp.json()["total_events"] == 1
        assert bob_resp.json()["total_events"] == 0


# ---------------------------------------------------------------------------
# Failsafe — telemetry must not break the main flow
# ---------------------------------------------------------------------------

class TestFailsafe:
    @pytest.mark.asyncio
    async def test_record_event_returns_none_on_unknown_event(self, db_session):
        """Unknown event type still persists (with 0 seconds) — no crash."""
        event = await record_event(db_session, "u1", "nonsense", run_id="r1")
        assert event is not None
        assert event.manual_seconds == 0

    @pytest.mark.asyncio
    async def test_record_event_failure_returns_none(self, db_session, monkeypatch):
        """If the DB commit fails, record_event swallows the error and returns None."""
        original_commit = db_session.commit

        async def broken_commit():
            raise RuntimeError("simulated DB failure")

        monkeypatch.setattr(db_session, "commit", broken_commit)
        result = await record_event(db_session, "u1", "capacity_run", sku_count=100, carrier_count=1)
        assert result is None
        # Restore so fixture teardown can roll back cleanly
        monkeypatch.setattr(db_session, "commit", original_commit)
