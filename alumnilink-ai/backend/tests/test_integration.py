"""
Integration test suite covering the full mentorship lifecycle, run against the
live docker-compose stack (real Postgres, real Redis, real backend process).

Run with:
    docker compose exec backend pytest tests/test_integration.py -v
"""

import asyncio

import redis.asyncio as redis

from app.config import settings
from app.core.redis_client import window_key

from tests.conftest import (
    register_student,
    register_alumni,
    login,
    approve_alumni_as_admin,
    auth_headers,
    unique_suffix,
)

GOOD_MESSAGE = (
    "Hi, I would love your guidance on breaking into data science. I saw your "
    "experience at your company and wanted to discuss your career journey, your "
    "background, and how you approached your first few years in the industry. "
    "Could we schedule a short session to talk about your path and any advice "
    "you would give someone starting out in this field?"
)
BAD_MESSAGE = "hey gimme a job asap"
SPAM_POST = "Click here now, guaranteed winner, buy now for free money today!"


# ---------------------------------------------------------------------------
# Test 1 — Auth flow
# ---------------------------------------------------------------------------
async def test_student_register_and_login(client, db_session):
    reg = await register_student(client, db_session)
    assert reg["access_token"]
    assert reg["user"]["role"] == "student"

    logged_in = await login(client, reg["_email"], reg["_password"])
    assert logged_in["access_token"]
    assert logged_in["refresh_token"]

    resp = await client.get("/api/v1/auth/me", headers=auth_headers(logged_in["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["email"] == reg["_email"]


# ---------------------------------------------------------------------------
# Test 2 — Alumni verification gate
#
# Note: this system's actual verification gate (see PROGRESS.md, Day 3) is NOT
# on login — a pending alumnus can log in immediately, same as a verified one.
# The gate sits on profile creation / availability listing instead, checked via
# `verification_status`. This test exercises the real gate rather than the
# "login returns 403 while pending" behavior, which this app deliberately does
# not implement.
# ---------------------------------------------------------------------------
async def test_alumni_pending_then_verified(client, db_session, admin_token):
    reg = await register_alumni(client, db_session)
    assert reg["user"]["verification_status"] == "pending"

    logged_in = await login(client, reg["_email"], reg["_password"])
    assert logged_in["access_token"]

    resp = await client.post(
        "/api/v1/profiles/alumni",
        json={
            "company": "Test Co",
            "designation": "Engineer",
            "industry": "Technology",
            "experience_years": 5,
            "skills": ["Python"],
            "about_me": "Testing the verification gate.",
        },
        headers=auth_headers(logged_in["access_token"]),
    )
    assert resp.status_code == 403

    await approve_alumni_as_admin(client, admin_token, reg["user"]["id"])

    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers(logged_in["access_token"]))
    assert me_resp.json()["verification_status"] == "verified"

    resp2 = await client.post(
        "/api/v1/profiles/alumni",
        json={
            "company": "Test Co",
            "designation": "Engineer",
            "industry": "Technology",
            "experience_years": 5,
            "skills": ["Python"],
            "about_me": "Testing the verification gate.",
        },
        headers=auth_headers(logged_in["access_token"]),
    )
    assert resp2.status_code == 201


# ---------------------------------------------------------------------------
# Test 3 — Profile + Matching
# ---------------------------------------------------------------------------
async def test_student_profile_and_matching(client, db_session):
    reg = await register_student(client, db_session)
    headers = auth_headers(reg["access_token"])

    resp = await client.post(
        "/api/v1/profiles/student",
        json={
            "department": "Data Science",
            "degree": "B.Sc",
            "graduation_year": 2027,
            "career_goal": "Become a machine learning engineer",
            "skills": ["Python", "Machine Learning"],
            "profile_description": "Interested in applied ML and recommendation systems.",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/matching/alumni", headers=headers)
    assert resp.status_code == 200
    matches = resp.json()
    assert len(matches) > 0
    for m in matches:
        assert 0.0 <= m["match_score"] <= 1.0
    scores = [m["match_score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Test 4 — Screener
# ---------------------------------------------------------------------------
async def test_screener_pass_and_fail(client, db_session):
    reg = await register_student(client, db_session)
    headers = auth_headers(reg["access_token"])

    good = await client.post("/api/v1/screener/check", json={"message": GOOD_MESSAGE}, headers=headers)
    assert good.status_code == 200
    good_body = good.json()
    assert good_body["passed"] is True
    assert good_body["score"] >= 0.6

    bad = await client.post("/api/v1/screener/check", json={"message": BAD_MESSAGE}, headers=headers)
    assert bad.status_code == 200
    bad_body = bad.json()
    assert bad_body["passed"] is False
    assert bad_body["score"] < 0.6

    assert set(good_body["breakdown"].keys()) == {
        "intent", "professional_tone", "personalisation", "message_quality"
    }


# ---------------------------------------------------------------------------
# Test 5 — Full mentorship lifecycle
# ---------------------------------------------------------------------------
async def test_full_mentorship_lifecycle(client, db_session, admin_token):
    student_reg = await register_student(client, db_session)
    student_headers = auth_headers(student_reg["access_token"])

    alumni_reg = await register_alumni(client, db_session)
    await approve_alumni_as_admin(client, admin_token, alumni_reg["user"]["id"])
    alumni_headers = auth_headers(alumni_reg["access_token"])

    await client.post(
        "/api/v1/profiles/student",
        json={
            "department": "Data Science", "degree": "B.Sc", "graduation_year": 2027,
            "career_goal": "Become a data analyst", "skills": ["SQL", "Python"],
            "profile_description": "Interested in analytics.",
        },
        headers=student_headers,
    )
    await client.post(
        "/api/v1/profiles/alumni",
        json={
            "company": "Test Co", "designation": "Analyst", "industry": "Finance",
            "experience_years": 6, "skills": ["SQL"], "about_me": "Happy to mentor.",
        },
        headers=alumni_headers,
    )

    slot_resp = await client.post(
        "/api/v1/availability/",
        json={"slot_date": "2026-08-01", "start_time": "10:00:00", "end_time": "10:30:00"},
        headers=alumni_headers,
    )
    assert slot_resp.status_code == 201
    slot_id = slot_resp.json()["id"]

    alumni_user_id = alumni_reg["user"]["id"]
    req_resp = await client.post(
        "/api/v1/requests/",
        json={"alumni_id": alumni_user_id, "message": GOOD_MESSAGE},
        headers=student_headers,
    )
    assert req_resp.status_code == 201
    request_id = req_resp.json()["request"]["id"]

    accept_resp = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=alumni_headers)
    assert accept_resp.status_code == 200
    window_id = accept_resp.json()["id"]

    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        ttl = await redis_client.ttl(window_key(window_id))
        assert ttl > 0
    finally:
        await redis_client.aclose()

    book_resp = await client.post(
        "/api/v1/sessions/book",
        json={"window_id": window_id, "slot_id": slot_id},
        headers=student_headers,
    )
    assert book_resp.status_code == 201
    session_id = book_resp.json()["id"]

    my_slots = await client.get("/api/v1/availability/my", headers=alumni_headers)
    booked_slot = next(s for s in my_slots.json() if s["id"] == slot_id)
    assert booked_slot["status"] == "booked"

    window_detail = await client.get(f"/api/v1/windows/{window_id}", headers=student_headers)
    assert window_detail.json()["status"] == "booked"

    complete_resp = await client.patch(f"/api/v1/sessions/{session_id}/complete", headers=alumni_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    feedback_resp = await client.post(
        f"/api/v1/sessions/{session_id}/feedback",
        json={"rating": 5, "comment": "Great session!"},
        headers=student_headers,
    )
    assert feedback_resp.status_code == 201

    student_view = await client.get(f"/api/v1/sessions/{session_id}/feedback", headers=student_headers)
    alumni_view = await client.get(f"/api/v1/sessions/{session_id}/feedback", headers=alumni_headers)
    assert student_view.status_code == 200 and len(student_view.json()) == 1
    assert alumni_view.status_code == 200 and len(alumni_view.json()) == 1


# ---------------------------------------------------------------------------
# Test 6 — Concurrency
# ---------------------------------------------------------------------------
async def test_concurrent_slot_booking(client, db_session, admin_token):
    alumni_reg = await register_alumni(client, db_session)
    await approve_alumni_as_admin(client, admin_token, alumni_reg["user"]["id"])
    alumni_headers = auth_headers(alumni_reg["access_token"])
    await client.post(
        "/api/v1/profiles/alumni",
        json={
            "company": "Test Co", "designation": "Analyst", "industry": "Finance",
            "experience_years": 6, "skills": ["SQL"], "about_me": "Happy to mentor.",
        },
        headers=alumni_headers,
    )
    slot_resp = await client.post(
        "/api/v1/availability/",
        json={"slot_date": "2026-08-02", "start_time": "14:00:00", "end_time": "14:30:00"},
        headers=alumni_headers,
    )
    slot_id = slot_resp.json()["id"]
    alumni_user_id = alumni_reg["user"]["id"]

    window_ids = []
    for _ in range(2):
        student_reg = await register_student(client, db_session)
        student_headers = auth_headers(student_reg["access_token"])
        await client.post(
            "/api/v1/profiles/student",
            json={
                "department": "Data Science", "degree": "B.Sc", "graduation_year": 2027,
                "career_goal": "Become a data analyst", "skills": ["SQL"],
                "profile_description": "Interested in analytics.",
            },
            headers=student_headers,
        )
        req_resp = await client.post(
            "/api/v1/requests/",
            json={"alumni_id": alumni_user_id, "message": GOOD_MESSAGE},
            headers=student_headers,
        )
        request_id = req_resp.json()["request"]["id"]
        accept_resp = await client.patch(f"/api/v1/requests/{request_id}/accept", headers=alumni_headers)
        window_ids.append((accept_resp.json()["id"], student_headers))

    results = await asyncio.gather(
        *[
            client.post("/api/v1/sessions/book", json={"window_id": wid, "slot_id": slot_id}, headers=headers)
            for wid, headers in window_ids
        ],
        return_exceptions=True,
    )
    status_codes = sorted(r.status_code for r in results)
    assert status_codes == [201, 409]


# ---------------------------------------------------------------------------
# Test 7 — Feed moderation
# ---------------------------------------------------------------------------
async def test_feed_moderation_pipeline(client, db_session):
    reg = await register_student(client, db_session)
    headers = auth_headers(reg["access_token"])
    marker = unique_suffix()

    clean_content = f"Sharing a great data science internship opportunity at a fintech startup. Ref {marker}."
    clean_resp = await client.post(
        "/api/v1/feed/posts",
        json={"content": clean_content, "post_type": "internship"},
        headers=headers,
    )
    assert clean_resp.status_code == 201
    assert clean_resp.json()["post"]["moderation_status"] == "approved"

    spam_content = f"{SPAM_POST} Ref {marker}"
    spam_resp = await client.post(
        "/api/v1/feed/posts",
        json={"content": spam_content, "post_type": "general"},
        headers=headers,
    )
    assert spam_resp.status_code == 400
    assert spam_resp.json()["detail"]["layer_failed"] == "spam_check"

    feed_resp = await client.get("/api/v1/feed/posts", params={"limit": 100})
    contents = [p["content"] for p in feed_resp.json()]
    assert clean_content in contents
    assert spam_content not in contents


# ---------------------------------------------------------------------------
# Test 8 — Admin analytics
# ---------------------------------------------------------------------------
async def test_admin_analytics(client, admin_token):
    resp = await client.get("/api/v1/admin/analytics/summary", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    expected_keys = {
        "total_students", "total_alumni", "pending_alumni", "total_requests",
        "accepted_requests", "rejected_requests", "total_sessions", "completed_sessions",
        "total_posts", "total_feedback", "avg_rating", "avg_match_score",
        "avg_screening_score", "verified_alumni", "acceptance_rate",
        "completion_rate", "avg_match_score_pct",
    }
    assert expected_keys.issubset(body.keys())


# ---------------------------------------------------------------------------
# Test 9 — Role enforcement
# ---------------------------------------------------------------------------
async def test_role_gates(client, db_session):
    student_reg = await register_student(client, db_session)
    alumni_reg = await register_alumni(client, db_session)

    resp = await client.get(
        "/api/v1/requests/incoming", headers=auth_headers(student_reg["access_token"])
    )
    assert resp.status_code == 403

    resp = await client.get(
        "/api/v1/matching/alumni", headers=auth_headers(alumni_reg["access_token"])
    )
    assert resp.status_code == 403

    resp = await client.get("/api/v1/sessions/my")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Test 10 — Predictive models
# ---------------------------------------------------------------------------
async def test_predictions(client, db_session, admin_token):
    alumni_reg = await register_alumni(client, db_session)
    await approve_alumni_as_admin(client, admin_token, alumni_reg["user"]["id"])
    alumni_headers = auth_headers(alumni_reg["access_token"])
    await client.post(
        "/api/v1/profiles/alumni",
        json={
            "company": "Test Co", "designation": "Analyst", "industry": "Finance",
            "experience_years": 6, "skills": ["SQL"], "about_me": "Happy to mentor.",
        },
        headers=alumni_headers,
    )

    student_reg = await register_student(client, db_session)
    student_headers = auth_headers(student_reg["access_token"])
    await client.post(
        "/api/v1/profiles/student",
        json={
            "department": "Data Science", "degree": "B.Sc", "graduation_year": 2027,
            "career_goal": "Become a data analyst", "skills": ["SQL"],
            "profile_description": "Interested in analytics.",
        },
        headers=student_headers,
    )

    resp = await client.get(
        f"/api/v1/predict/response/{alumni_reg['user']['id']}", headers=student_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["response_likelihood"] <= 1.0
    assert body["interpretation"] in {"High", "Medium", "Low"}
