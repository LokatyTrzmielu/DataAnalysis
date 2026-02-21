"""CLI seed script: initialize DB and create initial users/carriers."""

import asyncio
import sys

import bcrypt
from sqlalchemy import select

from api.database import Base, engine, SessionLocal
from api.models.user import User
from api.models.carrier import Carrier
from api.models import *  # noqa: F401, F403 — register all models with Base

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def init_db() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created.")


async def create_user(email: str, password: str, name: str) -> None:
    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User {email} already exists — skipping.")
            return
        user = User(
            email=email,
            name=name,
            password_hash=_hash_password(password),
        )
        db.add(user)
        await db.commit()
        print(f"Created user: {email}")


async def seed_carriers() -> None:
    """Seed predefined carriers from YAML into DB."""
    from src.core.carriers import CarrierService

    service = CarrierService()
    predefined = [c for c in service.load_all_carriers() if c.is_predefined]

    async with SessionLocal() as db:
        for c in predefined:
            existing = await db.execute(
                select(Carrier).where(Carrier.carrier_id == c.carrier_id)
            )
            if existing.scalar_one_or_none():
                continue
            db_carrier = Carrier(
                carrier_id=c.carrier_id,
                name=c.name,
                inner_length_mm=c.inner_length_mm,
                inner_width_mm=c.inner_width_mm,
                inner_height_mm=c.inner_height_mm,
                max_weight_kg=c.max_weight_kg,
                is_predefined=True,
                is_active=c.is_active,
                priority=c.priority,
            )
            db.add(db_carrier)
        await db.commit()
    print(f"Seeded {len(predefined)} predefined carriers.")


async def main() -> None:
    await init_db()
    await seed_carriers()

    # Create a default admin user if env vars are set or args provided
    args = sys.argv[1:]
    if len(args) == 3:
        email, password, name = args
        await create_user(email, password, name)
    else:
        print(
            "Tip: pass email password name as arguments to create a user:\n"
            "  python -m api.seed admin@example.com secret123 Admin"
        )


if __name__ == "__main__":
    asyncio.run(main())
