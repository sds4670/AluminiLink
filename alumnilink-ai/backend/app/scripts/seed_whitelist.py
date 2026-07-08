"""
Seed the allowed_students / allowed_alumni whitelist tables.

These tables gate registration in Module 1 (Auth): a student can only
self-register with a roll_number already present in `allowed_students`, and an
alumnus can only self-register with a register_number already present in
`allowed_alumni`.

Usage (from backend/, with the venv activated or inside the backend container):
    python -m app.scripts.seed_whitelist

Docker:
    docker compose exec backend python -m app.scripts.seed_whitelist

Idempotent: existing rows are cleared before the fixed seed set is inserted, so
re-running always leaves the table in the exact same state. Any users who
already registered against a previously seeded number are unaffected — the
whitelist entry is only a registration gate, not a live reference from users.
"""

import asyncio

from sqlalchemy import delete
from app.database import AsyncSessionLocal, create_all_tables
from app.models.allowed_student import AllowedStudent
from app.models.allowed_alumni import AllowedAlumni

STUDENT_ROLL_NUMBERS = [f"2024DS{str(i).zfill(3)}" for i in range(1, 21)]  # 2024DS001 .. 2024DS020
ALUMNI_REGISTER_NUMBERS = [f"REG2014DS{str(i).zfill(2)}" for i in range(1, 11)]  # REG2014DS01 .. REG2014DS10


async def seed() -> None:
    await create_all_tables()

    async with AsyncSessionLocal() as db:
        await db.execute(delete(AllowedStudent))
        await db.execute(delete(AllowedAlumni))

        db.add_all(
            AllowedStudent(roll_number=roll, full_name=f"Seed Student {i}")
            for i, roll in enumerate(STUDENT_ROLL_NUMBERS, start=1)
        )
        db.add_all(
            AllowedAlumni(register_number=reg, full_name=f"Seed Alumni {i}")
            for i, reg in enumerate(ALUMNI_REGISTER_NUMBERS, start=1)
        )

        await db.commit()

    print(f"Reseeded {len(STUDENT_ROLL_NUMBERS)} student roll numbers ({STUDENT_ROLL_NUMBERS[0]}..{STUDENT_ROLL_NUMBERS[-1]}).")
    print(f"Reseeded {len(ALUMNI_REGISTER_NUMBERS)} alumni register numbers ({ALUMNI_REGISTER_NUMBERS[0]}..{ALUMNI_REGISTER_NUMBERS[-1]}).")


if __name__ == "__main__":
    asyncio.run(seed())
