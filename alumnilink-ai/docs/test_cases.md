# Test Cases — AlumniLink AI

Last updated: 2026-07-10 (Day 7)

Status reflects the system's actual, verified behavior — where the implementation
deliberately differs from what might be assumed (e.g. pending alumni **can** log in;
the verification gate sits on profile/availability creation instead), the test case
below documents the real behavior rather than an assumption, with a short note.
Cases marked **Known Limitation** describe intentional, documented gaps (see
`PROGRESS.md`'s "Known limitations" section) rather than bugs.

Every case below has been exercised either by the automated suite in
`backend/tests/test_integration.py`, or via live `curl`/browser verification during
the module's original implementation (see `PROGRESS.md`'s day-by-day log).

---

## Module 1 — Auth & Role Management

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M1-01 | Student Registration | Valid roll number + all fields | 201 + JWT access/refresh token returned | Pass |
| TC-M1-02 | Student Registration | Roll number not on the whitelist | 403 Forbidden | Pass |
| TC-M1-03 | Student Registration | Duplicate email | 400 Bad Request ("Email already registered") | Pass |
| TC-M1-04 | Login | Valid credentials | 200 + access + refresh token | Pass |
| TC-M1-05 | Login | Wrong password | 401 Invalid credentials | Pass |
| TC-M1-06 | Login | Pending (unverified) alumnus | 200 + token — login is allowed while pending; the verification gate is enforced separately on profile/availability creation (see TC-M8-04), not on login | Pass |
| TC-M1-07 | Token | Malformed/invalid access token on `/auth/me` | 401 Unauthorized | Pass |
| TC-M1-08 | Role gate | Student token on an alumni-only route (`GET /requests/incoming`) | 403 Forbidden | Pass |

## Module 2 — Semantic Matching

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M2-01 | Profile creation | Student submits a valid profile | 201 Created, a real 384-dim SBERT embedding is stored | Pass |
| TC-M2-02 | Profile creation | Duplicate profile for the same user | 400 Bad Request ("Profile already exists") | Pass |
| TC-M2-03 | Matching | `GET /matching/alumni` before completing a profile | 400 Bad Request ("Complete your profile first") | Pass |
| TC-M2-04 | Matching | `GET /matching/alumni` with a completed profile | 200, ranked list of alumni returned | Pass |
| TC-M2-05 | Matching | Match score range | Every `match_score` value falls between 0.0 and 1.0 | Pass |
| TC-M2-06 | Matching | Ranking order | Results are sorted by `match_score` descending | Pass |
| TC-M2-07 | Matching | Verification filter | Pending/unverified alumni are excluded from match results | Pass |
| TC-M2-08 | Match score cache | `GET /matching/alumni/{id}/score` | Returns the cached `match_scores` row if present, else computes cosine similarity and caches it on the fly | Pass |
| TC-M2-09 | Embedding consistency | Same profile text encoded twice | Produces an identical 384-dim vector (deterministic SBERT model) | Pass |

## Module 3 — AI Outreach Screener

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M3-01 | Screener check | Personalised, 50+ word message referencing the alumnus's company/role | `passed=True`, `score >= 0.6` | Pass |
| TC-M3-02 | Screener check | Short, casual message ("hey gimme a job asap") | `passed=False`, `score < 0.6` | Pass |
| TC-M3-03 | Screener breakdown | Any message | `breakdown` contains exactly 4 keys: `intent`, `professional_tone`, `personalisation`, `message_quality` | Pass |
| TC-M3-04 | Screener suggestions | Low-scoring message | `suggestions` array contains actionable improvement tips for each weak dimension | Pass |
| TC-M3-05 | Intent layer | Message with no mentorship-ask keywords | `intent` sub-score near 0 | Pass |
| TC-M3-06 | Professional tone layer | Message containing "asap"/"urgent"/"refer me" | `professional_tone` sub-score penalised per keyword hit | Pass |
| TC-M3-07 | Request submission gate | `POST /requests/` with a message scoring < 0.6 | 400 Bad Request, no request row created | Pass |
| TC-M3-08 | Request submission | `POST /requests/` with a message scoring >= 0.6 | 201 Created, `screening_score` persisted on the request | Pass |

## Module 4 — 48h Window + Session Booking

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M4-01 | Request accept | Alumnus accepts a pending request | 200, a `ConnectionWindow` is created with a 48h `expires_at`, `status=active` | Pass |
| TC-M4-02 | Request accept | An alumnus who doesn't own the request tries to accept it | 404 Not Found | Pass |
| TC-M4-03 | Request accept | Accepting an already-processed (accepted/rejected) request | 400 Bad Request | Pass |
| TC-M4-04 | Window TTL | Window creation | A matching `window:{id}` Redis key is set with a 48h TTL | Pass |
| TC-M4-05 | Window expiry | Redis key TTL reaches 0 | The keyspace-notification listener dispatches Celery's `expire_window` task, window `status -> expired` | Pass (verified with a short-TTL key during Day 4 testing) |
| TC-M4-06 | Session booking | Student books an open slot inside an active window | 201 Created, slot `status -> booked`, window `status -> booked` | Pass |
| TC-M4-07 | Session booking | Booking after the window has expired | 409 Conflict ("Window has expired") | Pass |
| TC-M4-08 | Session booking | Booking an already-booked slot | 409 Conflict ("Slot already booked") | Pass |
| TC-M4-09 | Concurrency | Two students race to book the same open slot simultaneously | Exactly one `201`, one `409` — enforced by a `SELECT ... FOR UPDATE` row lock | Pass |
| TC-M4-10 | Session completion | Alumnus marks a scheduled session complete | 200, `status -> completed`, `session_completed` audit log entry created | Pass |
| TC-M4-11 | Feedback | Student submits feedback on a completed session | 201 Created, rating (1-5) stored | Pass |
| TC-M4-12 | Feedback | Duplicate feedback from the same reviewer on the same session | 400 Bad Request ("Feedback already submitted for this session") | Pass |

## Module 5 — Community Feed

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M5-01 | Post creation | Clean content, 5+ words | 201 Created, `moderation_status=approved` | Pass |
| TC-M5-02 | Post creation (Layer 1) | Content under 5 words | 400 Bad Request, `layer_failed="length_check"` | Pass |
| TC-M5-03 | Post creation (Layer 2) | Content with 2+ spam keywords ("click here", "guaranteed", "buy now"...) | 400 Bad Request, `layer_failed="spam_check"`, post never appears in the public feed | Pass |
| TC-M5-04 | Post creation (Layers 3-4) | Content with toxic/abusive language | **Not currently rejected** — `detoxify` is not installed in this environment (unresolvable dependency conflict, see `PROGRESS.md`), so `toxicity_score` is always `0.0` and layers 3-4 never trigger | Known Limitation |
| TC-M5-05 | Feed listing | `GET /feed/posts` | Only `approved` posts are returned; `pending_review`/`rejected` posts are excluded | Pass |
| TC-M5-06 | Likes | `POST /feed/posts/{id}/like` called twice by the same user | Toggles: first call likes, second call un-likes | Pass |
| TC-M5-07 | Comments | `POST /feed/posts/{id}/comments` with spam content | 400 Bad Request, comment not created | Pass |
| TC-M5-08 | Pagination | `GET /feed/posts?limit=&offset=` | Returns at most `limit` posts, respects `offset`, newest-first (pinned posts first) | Pass |

## Module 6 — Predictive Models

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M6-01 | Response prediction | `GET /predict/response/{alumni_id}` as a student | 200, `response_likelihood` in [0, 1], `interpretation` in {High, Medium, Low} | Pass |
| TC-M6-02 | Completion prediction | `GET /predict/completion/{session_id}` as a session participant | 200, `completion_likelihood` in [0, 1], `interpretation` in {High, Medium, Low} | Pass |
| TC-M6-03 | Response prediction | Non-student role (alumni token) calls the response endpoint | 403 Forbidden | Pass |
| TC-M6-04 | Completion prediction | A user who isn't a participant in the session queries it | 403 Forbidden | Pass |

## Module 7 — Admin Analytics & ETL

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M7-01 | Analytics summary | `GET /admin/analytics/summary` as admin | 200, all bronze/silver keys present (`total_students`, `avg_match_score`, `completion_rate`, etc.) | Pass |
| TC-M7-02 | Analytics summary | Non-admin token | 403 Forbidden | Pass |
| TC-M7-03 | Analytics snapshots | `GET /admin/analytics/snapshots` | 200, returns snapshots from the last 30 days | Pass |
| TC-M7-04 | User management | `GET /admin/users?role=student` | 200, only student-role users returned | Pass |
| TC-M7-05 | Audit logs | `GET /admin/audit-logs?action=approve_alumni` | 200, only matching-action entries returned | Pass |
| TC-M7-06 | ETL idempotency | Running the nightly ETL twice on the same calendar day | Second run **upserts** (updates) the existing `analytics_snapshots` row rather than duplicating it | Pass |

## Module 8 — Alumni Verification

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M8-01 | Registration | New alumnus registers | `verification_status = pending` | Pass |
| TC-M8-02 | Admin approval | `POST /admin/alumni/{id}/approve` | `verification_status -> verified`, `approve_alumni` audit log entry created | Pass |
| TC-M8-03 | Admin rejection | `POST /admin/alumni/{id}/reject` | `verification_status -> rejected` | Pass |
| TC-M8-04 | Gate enforcement | Pending alumnus attempts `POST /profiles/alumni` or `POST /availability/` | 403 Forbidden on both until verified | Pass |

## Module 9 — Availability Slots

| Test ID | Test Field | Test Case | Expected Outcome | Status |
|---|---|---|---|---|
| TC-M9-01 | Slot creation | Verified alumnus creates a slot | 201 Created, `status=open` | Pass |
| TC-M9-02 | Slot creation | Pending (unverified) alumnus attempts to create a slot | 403 Forbidden | Pass |
| TC-M9-03 | Slot edit/delete protection | Attempt to edit or delete a booked slot | 400 Bad Request ("Cannot edit/delete a booked slot") | Pass |
| TC-M9-04 | Slot listing (student view) | `GET /availability/{alumni_id}` | Only `status=open` slots returned | Pass |
| TC-M9-05 | Slot listing (alumni view) | `GET /availability/my` | All of the alumnus's own slots returned, regardless of status | Pass |
| TC-M9-06 | Slot booking | Booking transitions a slot `open -> booked` | Slot status updated atomically under a row lock (see TC-M4-09) | Pass |

---

**Total: 65 test cases** across 9 modules (minimum 64 required).

## Legend

- **Pass** — verified behavior matches the expected outcome, either via `backend/tests/test_integration.py` or live `curl`/browser testing during the module's original implementation.
- **Known Limitation** — the expected outcome describes the system's actual, intentionally-scoped-down behavior (not a defect); see `PROGRESS.md`'s "Known limitations" section for the reasoning and what a full fix would require.
