"""
Shared fixtures for the integration test suite.

These tests exercise the *real*, already-running stack (the same backend,
Postgres, and Redis containers `docker compose up` starts) rather than an
isolated in-memory app instance — that's deliberate, since the goal is to
prove the deployed system works end-to-end, not just the ASGI app in a
vacuum. Every test that needs a student/alumni account registers its own
throwaway user (unique email + a whitelist row inserted on the fly) so the
suite is safe to re-run against the pilot-seeded database without colliding
with or depending on the seeded demo accounts.
"""

import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.allowed_student import AllowedStudent
from app.models.allowed_alumni import AllowedAlumni
from app.models.user import User

# pytest-asyncio (in the default "auto" mode used here) gives every test
# function its own fresh event loop. The app's own module-level engine pools
# asyncpg connections across calls, so reusing it here would bind a connection
# to test 1's loop and then blow up when test 2's (different) loop tries to use
# it. NullPool sidesteps that entirely: every checkout opens a brand new
# connection on whatever loop is currently running, so nothing outlives a
# single test.
test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")

ADMIN_EMAIL = "testadmin@christuniversity.in"
ADMIN_PASSWORD = "Passw0rd!"

_created_user_ids: list[int] = []
_created_student_whitelist_ids: list[int] = []
_created_alumni_whitelist_ids: list[int] = []


def unique_suffix() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
async def client():
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


async def register_student(client: AsyncClient, db, **overrides) -> dict:
    """Inserts a fresh whitelist row, registers a student, returns the register response JSON."""
    suffix = unique_suffix()
    roll_number = overrides.get("roll_number", f"TEST-STU-{suffix}")
    email = overrides.get("email", f"test.student.{suffix}@christuniversity.in")

    allowed = AllowedStudent(roll_number=roll_number, full_name="Test Student")
    db.add(allowed)
    await db.commit()
    await db.refresh(allowed)
    _created_student_whitelist_ids.append(allowed.id)

    payload = {
        "email": email,
        "password": "Passw0rd!",
        "full_name": overrides.get("full_name", "Test Student"),
        "role": "student",
        "roll_number": roll_number,
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    _created_user_ids.append(body["user"]["id"])
    body["_password"] = payload["password"]
    body["_email"] = email
    return body


async def register_alumni(client: AsyncClient, db, **overrides) -> dict:
    """Inserts a fresh whitelist row, registers an alumnus, returns the register response JSON."""
    suffix = unique_suffix()
    register_number = overrides.get("register_number", f"TEST-ALU-{suffix}")
    email = overrides.get("email", f"test.alumni.{suffix}@alumni.christuniversity.in")

    allowed = AllowedAlumni(register_number=register_number, full_name="Test Alumnus")
    db.add(allowed)
    await db.commit()
    await db.refresh(allowed)
    _created_alumni_whitelist_ids.append(allowed.id)

    payload = {
        "email": email,
        "password": "Passw0rd!",
        "full_name": overrides.get("full_name", "Test Alumnus"),
        "role": "alumni",
        "register_number": register_number,
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    _created_user_ids.append(body["user"]["id"])
    body["_password"] = payload["password"]
    body["_email"] = email
    return body


async def login(client: AsyncClient, email: str, password: str) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(scope="session")
async def admin_token():
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        body = await login(ac, ADMIN_EMAIL, ADMIN_PASSWORD)
        return body["access_token"]


async def approve_alumni_as_admin(client: AsyncClient, admin_token: str, user_id: int) -> None:
    resp = await client.post(
        f"/api/v1/admin/alumni/{user_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
async def _cleanup_test_data():
    yield
    async with TestSessionLocal() as db:
        from sqlalchemy import delete

        if _created_user_ids:
            await db.execute(delete(User).where(User.id.in_(_created_user_ids)))
            _created_user_ids.clear()
        if _created_student_whitelist_ids:
            await db.execute(delete(AllowedStudent).where(AllowedStudent.id.in_(_created_student_whitelist_ids)))
            _created_student_whitelist_ids.clear()
        if _created_alumni_whitelist_ids:
            await db.execute(delete(AllowedAlumni).where(AllowedAlumni.id.in_(_created_alumni_whitelist_ids)))
            _created_alumni_whitelist_ids.clear()
        await db.commit()
