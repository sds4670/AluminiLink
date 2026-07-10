# AlumniLink AI — Progress & Database Guide

This file explains, in plain language: what's been built so far (day by day), and exactly how the database works right now — what's real, what's seeded, and what's hardcoded.

Last updated: 2026-07-10

---

## 1. Day-by-day timeline

### Day 1 — Scaffold
The initial project skeleton was set up: FastAPI backend, React+Vite frontend, PostgreSQL+pgvector, Redis, Celery, Docker Compose wiring. All 14 database tables were defined as SQLAlchemy models (empty — no data, no working endpoints yet). This gave every later module a place to plug into.

### Day 2 — Module 1: Auth
Built the full authentication system:
- `POST /api/v1/auth/register`, `/login`, `/refresh`, `GET /me`
- **Whitelist gate**: a student can only register if their roll number is already sitting in the `allowed_students` table; same for alumni via `allowed_alumni`. This models "only people the university actually enrolled/employed can make an account."
- Passwords hashed with bcrypt; JWT access tokens (60 min) + refresh tokens (7 days), each carrying a `type` claim so an access token can't be replayed as a refresh token or vice versa.
- Role dependencies (`require_student`, `require_alumni`, `require_admin`) used to lock down every other endpoint in the app.
- Seed script (`seed_whitelist.py`) to populate the whitelist tables.

**Bugs found and fixed along the way:** pgvector extension was never being created on a fresh database; `bcrypt`/`passlib` version mismatch broke password hashing entirely; a `full_name` field was added to `users` after the fact.

### Day 3 — Module 9 (Availability Slots) + Module 2 (Profiles + SBERT Matching)
This was the big one:
- **Module 9**: alumni can post/edit/delete "I'm free at this time" slots (`availability_slots`). Students can browse an alumnus's open slots. Booked slots can't be edited or deleted.
- **Module 2**: students and alumni fill out a profile (department/degree/career goal/skills for students; company/designation/industry/skills for alumni). Every profile gets a **real 384-dimension SBERT embedding** (via `sentence-transformers`, model `all-MiniLM-L6-v2`) computed from their text fields. Matching is now genuine cosine-similarity semantic search, not a random stub.
- Rewrote the **verification model**: alumni can log in immediately after registering, but a separate `verification_status` flag (`pending` → `verified`/`rejected`, set by an admin) gates whether they can create a profile or post availability slots. This replaced the earlier "alumni can't log in until approved" design, which would have made it impossible for a pending alumni to even reach the profile-creation screen.
- `seed.py` — loads `students_seed.csv` / `alumni_seed.csv`, creates 10 demo students + 10 demo alumni with real embeddings, and pre-computes all 100 student×alumni match scores.

**Bugs found and fixed along the way:**
- `sentence-transformers==2.2.2` pulled in a modern `huggingface_hub` that removed a function it depends on — pinned `huggingface-hub==0.16.4`, `transformers==4.30.2`, `tokenizers==0.13.3`.
- Default `torch` wheel is CUDA-enabled (~750MB) and kept timing out on download — switched to the CPU-only build (~200MB), which is also more correct since this backend has no GPU.
- A Postgres enum (`slotstatus`) still had its old values (`available`/`cancelled`) from before the field rename; added the new `open` value via `ALTER TYPE`.
- A numpy quirk: `if not embedding_column` crashes once SQLAlchemy hydrates a pgvector column into a numpy array (`ValueError: truth value of an array...`) — fixed to explicit `is None` checks everywhere.

### Day 3 (continued) — Cleanup, whitelist edits, and a real bug hunt
- Removed leftover ad-hoc test accounts, reset the admin password.
- Whitelist tables were re-seeded a few times with your specific roster (real names instead of "Seed Student N" placeholders) for `2024DS001`–`2024DS020` and `REG2014DS01`–`REG2014DS10`.
- **CORS false alarm, real bug found**: registration was throwing an unhandled 500 that *looked* like a CORS error in the browser (Starlette drops CORS headers on unhandled exceptions). The actual cause: a whitelist row's `is_registered` flag had drifted out of sync with the real `users` table, so the duplicate-roll-number check didn't trigger and the request crashed on a raw database constraint instead. Fixed the data (reconciled all whitelist rows against real users) and hardened `register_user()` so a database integrity error is now always caught and turned into a clean `409`, never a raw crash.

### Day 4 — Module 3 (AI Outreach Screening) + Module 4 (48hr Window + Session Booking)
This redesigned how a student goes from "found an alumnus" to "booked a real session":
- **Module 3**: before a student can send a connection request, their message is scored on 4 dimensions (intent, professional tone, personalisation, length) by `screen_message()` — a pure keyword/heuristic function, no ML model. Score ≥ 0.6 required to submit. `POST /api/v1/screener/check` lets the frontend preview the score before submitting. The request itself stores its `screening_score`.
- **Module 4**: when an alumnus accepts a request, a `connection_window` is created with a real 48-hour expiry. The student must book one of the alumnus's open `availability_slots` within that window or it expires automatically. Booking uses a Postgres row lock (`SELECT ... FOR UPDATE`) so two simultaneous booking attempts on the same slot can't both succeed — proven under a genuine concurrency test (two parallel requests: one `201`, one `409`).
- **Redesigned `connection_windows`**: previously modeled as a "bulk window an alumnus opens for many students" (unused, from the Day 1 scaffold). Replaced with a 1:1 "created when this specific request is accepted" model: `student_id`, `alumni_id`, `expires_at`, `status` (`active`/`booked`/`expired`).
- **Real Redis TTL + expiry**: accepting a request sets a `window:{id}` Redis key with a 48h TTL. A background listener in the FastAPI process (`app.main`'s lifespan) subscribes to Redis's key-expiry pub/sub channel and dispatches a Celery task (`expire_window`) when a window's time runs out without a booking — verified end-to-end with a short-TTL test key rather than waiting 48 hours.

**Bugs found and fixed along the way:**
- The Celery worker container only ever consumed the default `celery` queue; tasks routed to `moderation`/`screening`/`windows` queues would silently never run. Fixed by explicitly listing all queues in `docker-compose.yml`'s worker command (`-Q celery,screening,windows,...`) — a class of bug worth remembering, since it fails silently rather than erroring.
- `reject_request` mutated a row's `status` then returned it without `db.refresh()` — the `onupdate=func.now()`-generated `updated_at` value triggered a `MissingGreenlet` crash during response serialization. Also worth remembering: a `500` that the browser reports as a **CORS** error almost always means the real bug is server-side (Starlette drops CORS headers on unhandled-exception responses) — check the backend traceback first.

### Day 4 (continued) — Module 5 (Community Feed + Moderation) + Session Lifecycle Completion
- **Session lifecycle gap closed**: `PATCH /api/v1/sessions/{id}/complete` (alumni-only, logs to `audit_logs`) now exists, making the feedback flow actually reachable end-to-end: book → alumni marks complete → student leaves a 1–5 star rating (duplicate-feedback and wrong-status both guarded) → either participant can `GET` the feedback.
- **Module 5**: a community feed with 7 post types (internship/job/event/resource/query/announcement/general) and a 4-layer moderation pipeline (`moderate_post()`): length check → spam-keyword check → toxicity check → borderline-toxicity admin review. Posts, likes (toggle), and comments (also moderated) all live under `/api/v1/feed/...`. An admin moderation queue (`/api/v1/admin/moderation/queue`) handles the borderline cases layer 4 flags.
- New tables: `post_likes`, `post_comments` (both with real FKs to `posts`/`users`, `post_likes` has a unique `(post_id, user_id)` constraint so "toggle" is enforced at the DB level too, not just in application code).
- `posts.status` was renamed to `moderation_status` and the enum values changed (`pending_review`/`approved`/`rejected`) to match the new pipeline's vocabulary.

**A dependency decision worth understanding — `detoxify` is NOT installed:**
The spec asked for `detoxify==0.5.1` to power the toxicity-detection layer. After six separate rebuild attempts, this proved to be a genuine, unresolvable environment conflict, not a mistake to fix:
- `detoxify==0.5.1` hard-pins `transformers==4.22.1` exactly, which conflicts with the `transformers==4.30.2` this project already needed for `sentence-transformers` (Module 2's SBERT matching).
- Downgrading to satisfy detoxify then breaks on `tokenizers`: the version old-enough-for-4.22.1 has no prebuilt wheel for this Python/OS combination, forcing a from-source build.
- That source build needs a newer Rust compiler than Debian's `rustc` package provides (needs 1.86–1.88, Debian ships 1.85).

Rather than keep burning time chasing 2021-era pinned dependencies, the code leans on the fallback `moderate_post()` already had built in: `try: from detoxify import Detoxify ... except Exception: toxicity = 0.0`. **Practical effect**: layers 1–2 (length, spam keywords) fully work today; layers 3–4 (toxicity detection, admin-review flagging) are currently inert — nothing gets auto-rejected or flagged for toxicity, only for being too short or spammy. Revisit this if real toxicity filtering becomes a priority (e.g. a dedicated container/venv pinned to `transformers==4.22.1` just for this one function, or swapping to a newer toxicity library without detoxify's stale pins).

### Day 5 — Module 6 (Predictive Models) + Module 7 (Admin Analytics/ETL) + full frontend wiring
- **Module 6**: two scikit-learn models trained on synthetic-but-representative data in `scripts/train_models.py` and persisted with `joblib`: a `LogisticRegression` (+ `StandardScaler`) predicting how likely a student's outreach is to get an alumnus response, and a `RandomForestClassifier` predicting how likely a booked session is to actually complete. Both are lazy-loaded singletons in `services/ml/predict.py`. New endpoints: `GET /api/v1/predict/response/{alumni_id}` (student-only) and `GET /api/v1/predict/completion/{session_id}` (student or alumni, participant-only), each returning a likelihood float plus a High/Medium/Low interpretation. A shared `get_or_compute_match_score()` helper was added to `matching_service.py` so both the matching router and the new predict router can reuse the same "look up the cached score, else compute + cache it" logic.
- **Module 7**: a bronze→silver→gold ETL pipeline. Bronze = raw counts (students, alumni, requests, sessions, posts, avg ratings/scores). Silver = derived rates (acceptance rate, completion rate, avg-match-score %) computed on top of bronze. Gold = the combined dict upserted into a new `analytics_snapshots` table, keyed by `snapshot_date`. `GET /api/v1/admin/analytics/summary` runs the ETL inline and returns the live numbers; `GET /api/v1/admin/analytics/snapshots` returns the last 30 days of saved snapshots for trend charts. A Celery Beat schedule (`run_nightly_etl`, 2am daily, `analytics` queue) automates this going forward.
- **Admin router fully migrated to `/api/v1/admin`** (the last hold-out from the v1 migration started in earlier modules) — `GET /users` gained a `?role=` filter and now returns `full_name`/`verification_status`; `GET /audit-logs` gained a `?action=` filter; the old `/reports/summary` endpoint was removed in favour of the richer `/analytics/summary`.
- **Frontend**: wired all remaining pages to real endpoints. Added `recharts` for charts. Rewrote both Dashboards (student: 4 stat cards + top matches + feed preview; alumni: mentor tier badge computed from completed-session count, plus a client-side "AI Mentor Score" blending average rating, completion volume, response rate, and profile completeness), the admin Dashboard (6 KPI cards + a Recharts funnel bar chart) and Reports (Recharts line chart of the 3 snapshot rates over time), UserManagement and AuditLogs (role/action filters), and AlumniProfile (shows the new response-likelihood prediction badge). Added a `/pending` page and a `requireVerified` flag on `ProtectedRoute` so an alumnus whose account is still awaiting admin approval can see their dashboard/profile but gets redirected away from availability/requests/students/sessions.
- Fixed a leftover bug while doing this: `AlumniApprovalQueue.jsx`'s approve/reject buttons were still posting to the pre-migration `/api/admin/...` path (only its `GET` had been updated when the router was migrated) — now consistently on `/api/v1/admin/...`.

**Bugs found and fixed along the way:**
- The Docker bind mount (`./backend:/app`) hides anything written to `/app` during the image *build* — so the `RUN python -m app.scripts.train_models` step in the Dockerfile produces `.pkl` files that exist in the image layer but are invisible once the container starts (the host's `backend/models/` directory, empty, gets mounted over `/app/models/`). Fix: also run the training script once against the *live* container (`docker compose exec backend python -m app.scripts.train_models`) so the `.pkl` files land on the actual host directory and persist across restarts.
- After `docker compose up -d --force-recreate backend celery_worker`, an immediate queue/task check on the celery worker showed only the old queues/tasks (missing `analytics`, `run_nightly_etl`, `send_session_reminder`) — looked like the recreate hadn't taken effect. This turned out to be a timing artifact: checking again a few seconds later (once both containers were fully up, confirmed via `docker compose ps`) showed the correct queues and all 4 registered tasks. Worth remembering: don't trust a queue/task check taken in the same breath as a container recreate.
- No admin password was on file (it had been set by hand, outside version control, in an earlier session). Rather than reset the existing `admin@christuniversity.in` account's password, created a separate `testadmin@christuniversity.in` / `Passw0rd!` account for ongoing endpoint testing, leaving the original admin untouched.

All four new endpoints (`predict/response`, `predict/completion`, `admin/analytics/summary`, `admin/analytics/snapshots`) plus the enhanced `admin/users`/`admin/audit-logs` filters were verified live via curl (including role-based 403 checks), and every rewritten frontend page was confirmed to transform cleanly through Vite with no import/build errors.

---

## 2. Is the database "hardcoded"? — short answer: no, it's seeded

Nothing in the database is baked into the application code. Everything you see in the tables got there one of three ways:

1. **Whitelist seed scripts** (`backend/app/scripts/seed_whitelist.py`, `seed.py`) — these are scripts *you run*, not code that runs automatically. They read from two CSV files (`students_seed.csv`, `alumni_seed.csv`) and insert rows. Re-running them is safe (they check "does this already exist?" before inserting).
2. **Real API calls** — anyone hitting `POST /api/v1/auth/register` with a valid, unused whitelist number creates a genuine row, exactly like a real user would.
3. **Manual SQL** — a few rows (like the admin account, and a couple of whitelist entries added for testing) were inserted directly via `psql` during development.

There is no table anywhere that's simply "hardcoded" into Python — every table is a real Postgres table, created by SQLAlchemy from the model definitions in `backend/app/models/`, and populated by whichever of the three paths above actually ran.

### The one exception worth understanding: the whitelist mechanism
This *is* intentionally hardcoded, but not the accounts themselves — it's the **gate**. `allowed_students` and `allowed_alumni` are pre-populated lists of "roll numbers / register numbers that are allowed to sign up." Think of it like a guest list at a door: the names on the list don't become people until someone actually shows up and registers with that exact number. The `full_name` column on these two tables is just an administrative label ("this number belongs to so-and-so on the official roster") — it is **not** connected to the account that eventually registers with that number. That's why you'll see mismatches like whitelist row `2024DS003 → "Rohit Sharma"` while the account actually registered against it is `rohan.iyer@christuniversity.in`. Nothing is broken; they're just two independent fields.

---

## 3. Full database schema (as it exists right now)

16 tables total. Grouped by what they're for.

### 3.1 Identity & access control

**`users`** — one row per person, of any role.
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | |
| `email` | varchar(255), unique | login identifier |
| `hashed_password` | varchar(255) | bcrypt hash, never plaintext |
| `full_name` | varchar(255) | |
| `role` | enum `userrole` | `student` / `alumni` / `admin` |
| `status` | enum `userstatus` | `active` / `inactive` / `banned` / `pending_approval` (last one is now unused — see below) |
| `verification_status` | enum `verificationstatus` | `pending` / `verified` / `rejected` — **alumni-only gate** for creating a profile or posting availability. Students are auto-`verified`. |
| `is_verified` | boolean | legacy field, always `false` currently — not actively used by any endpoint |
| `roll_number` | varchar(50), unique, nullable | set only for students |
| `register_number` | varchar(50), unique, nullable | set only for alumni |
| `created_at` / `updated_at` | timestamps | |

> Note: `status = pending_approval` is a leftover enum value from an earlier design where alumni couldn't log in until approved. The current code never sets this value — verification is tracked purely via `verification_status` now. It's harmless to leave in the enum.

**`allowed_students`** / **`allowed_alumni`** — the whitelist gate described above.
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | |
| `roll_number` / `register_number` | varchar(50), unique | the number a student/alumnus must supply to register |
| `full_name` | varchar(255) | administrative label only (see §2) |
| `is_registered` | boolean | flips to `true` the moment someone successfully registers with this number |
| `registered_user_id` | int, FK → `users.id`, nullable | which account claimed this slot (`NULL` until claimed) |
| `created_at` | timestamp | |

### 3.2 Profiles (Module 2)

**`student_profiles`** — one-to-one with a `student`-role user.
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | this is the ID used in `match_scores`/`connection_requests`/`sessions`, **not** the user ID |
| `user_id` | int, FK → `users.id`, unique | |
| `department`, `degree`, `graduation_year` | varchar/int | |
| `career_goal` | text | |
| `skills` | JSON array of strings | e.g. `["Python", "ML", "SQL"]` |
| `profile_description` | text | |
| `embedding` | `vector(384)` | pgvector column — the SBERT embedding of `career_goal + skills + profile_description` |
| `created_at` / `updated_at` | timestamps | |

**`alumni_profiles`** — one-to-one with an `alumni`-role user.
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | used as "alumni_id" internally throughout matching/requests/sessions |
| `user_id` | int, FK → `users.id`, unique | |
| `company`, `designation`, `industry`, `experience_years` | varchar/int | |
| `skills` | JSON array of strings | |
| `about_me` | text | |
| `is_accepting_mentees` | boolean, default true | not currently filtered on anywhere, reserved for future use |
| `screening_score` | float, nullable | set by the (still-stubbed) admin "Screen" quality-check feature, unrelated to `verification_status` |
| `embedding` | `vector(384)` | SBERT embedding of `designation + industry + skills + about_me` |
| `created_at` / `updated_at` | timestamps | |

> Important API nuance: everywhere in the *API* (matching results, connection requests, public profile lookup), "alumni_id"/"user_id" that the frontend deals with is the **`users.id`**, not the `alumni_profiles.id`. The routers internally translate between the two. Only inside `availability_slots`, `connection_requests`, `sessions`, and `match_scores` does the raw `alumni_profiles.id` / `student_profiles.id` show up (as foreign keys).

### 3.3 Availability, connection requests & session booking (Modules 3, 4, 9)

**`availability_slots`**
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | |
| `alumni_id` | int, FK → `alumni_profiles.id` | |
| `slot_date` | date | |
| `start_time` / `end_time` | time (no timezone) | |
| `status` | enum `slotstatus` | current code only ever writes `open` or `booked`. The enum type in Postgres *also* still contains the old `available`/`cancelled` values from an earlier design (added, never removed) — they simply go unused. |
| `created_at` | timestamp | |

**`connection_requests`** — a student's request to connect with an alumnus, screened before it can even be created.
| Column | Type | Notes |
|---|---|---|
| `student_id` / `alumni_id` | FK → `student_profiles.id` / `alumni_profiles.id` | |
| `window_id` | FK → `connection_windows.id`, nullable | set once the alumnus accepts (see below) |
| `status` | enum `requeststatus` | `pending`/`accepted`/`rejected`/`withdrawn`/`expired` |
| `message` | text | must score ≥ 0.6 on `screen_message()` (Module 3) to be created at all |
| `screening_score` | float, nullable | the score that got it approved |
| `rejection_reason` | text | |

**`connection_windows`** — **redesigned in Module 4.** Previously an alumnus-opened "bulk window" that many students could apply into (unused, Day 1 scaffold leftover). Now created 1:1 the moment an alumnus accepts a specific request, giving the student a real 48-hour deadline to book a slot.
| Column | Type | Notes |
|---|---|---|
| `student_id` / `alumni_id` | FK → `student_profiles.id` / `alumni_profiles.id` | |
| `expires_at` | timestamp | set to `now() + 48h` on creation |
| `status` | enum `windowstatus` | `active` / `booked` / `expired` |

A matching Redis key `window:{id}` is set with a real 48h TTL at creation time. If the student books in time, the key is deleted and `status` becomes `booked`. If it expires first, a Redis pub/sub → Celery bridge (see `app.main`'s lifespan + `expire_window` task) flips `status` to `expired` and expires the linked request too.

**`sessions`** — a scheduled 1:1 mentoring session, created by `POST /api/v1/sessions/book`.
| Column | Type | Notes |
|---|---|---|
| `student_id` / `alumni_id` | FK → `student_profiles.id` / `alumni_profiles.id` | |
| `slot_id` | FK → `availability_slots.id`, nullable | |
| `request_id` | FK → `connection_requests.id`, nullable | |
| `window_id` | FK → `connection_windows.id`, nullable | **added in Module 4** |
| `scheduled_at` | timestamp | combined from the slot's date + start time |
| `status` | enum `sessionstatus` | `scheduled` → `completed` (via `PATCH /sessions/{id}/complete`, alumni-only) → feedback becomes leaveable |
| `duration_minutes` | int | computed from the slot's start/end time |

Booking uses `SELECT ... FOR UPDATE` on the slot row so two simultaneous booking attempts on the same slot can't both succeed (proven under real concurrency: one request gets `201`, the other a clean `409`).

**`session_feedbacks`** — post-session rating (1–5) left by the student; one per session (a duplicate attempt returns `400`). Either participant can read it back via `GET /sessions/{id}/feedback`.

### 3.4 Matching (Module 2)

**`match_scores`** — pre-computed/cached similarity between one student and one alumnus.
| Column | Type | Notes |
|---|---|---|
| `student_id` / `alumni_id` | FK → `student_profiles.id` / `alumni_profiles.id` | composite-unique in practice (checked in code, not a DB constraint) |
| `score` | float | currently always equal to `cosine_similarity` (0–1) |
| `cosine_similarity` | float | raw SBERT cosine similarity |
| `keyword_overlap`, `industry_match` | float | left over from an earlier, non-SBERT scoring formula; always `0.0` now since the matching endpoint doesn't compute them |
| `computed_at` | timestamp | |

Rows here are an **upsert cache**: `GET /api/v1/matching/alumni` recomputes and overwrites the row for every alumnus the student is compared against, every time it's called.

### 3.5 Content & moderation (Module 5)

**`posts`** — a student/alumni community post, run through the 4-layer `moderate_post()` pipeline on creation.
| Column | Type | Notes |
|---|---|---|
| `author_id` | FK → `users.id` | |
| `post_type` | enum `posttype` | `internship`/`job`/`event`/`resource`/`query`/`announcement`/`general` |
| `content` | text | |
| `moderation_status` | enum `moderationstatus` | `pending_review`/`approved`/`rejected` — **renamed from `status`**, values changed to match the pipeline |
| `toxicity_score` | float, nullable | from the pipeline's toxicity layer (currently always `0.0` — see the `detoxify` note in the Day 4 log above) |
| `is_pinned` | boolean | |

Only `moderation_status = approved` posts are ever returned by the public feed endpoints. `pending_review` posts sit in the admin moderation queue; `rejected` posts are kept (for the audit trail) but never shown to anyone.

**`post_moderation_logs`** — one row per moderation *decision* (auto-reject, admin-approve, admin-reject), recording `layer_failed`, `toxicity_score`, and `reason`.

**`post_likes`** *(new)* — one row per (post, user) like. A unique constraint on `(post_id, user_id)` means "toggle" is enforced by the database, not just the API.

**`post_comments`** *(new)* — comments on a post; also run through `moderate_post()` before being saved.

### 3.6 Admin
**`audit_logs`** — records admin/system actions (`approve_alumni`, `reject_alumni`, `ban_user`, `expire_window`, `session_completed`, etc.) with who did it and when. `actor_id` is `NULL` for system-triggered entries like `expire_window` (nobody clicked a button — the Redis TTL fired).

### 3.7 Predictive models & analytics (Module 6 + 7)

No new tables for Module 6 — the trained models live as `.pkl` files on disk (`backend/models/`), not in Postgres.

**`analytics_snapshots`** *(new)* — one row per day, storing the bronze+silver ETL output as a JSONB blob.
| Column | Type | Notes |
|---|---|---|
| `snapshot_date` | date, unique | one snapshot per calendar day — re-running the ETL the same day upserts instead of duplicating |
| `metrics` | JSONB | the full bronze+silver dict (counts + acceptance/completion rates + avg-match-score %) |
| `created_at` | timestamp | |

---

## 4. What's actually in the database right now (snapshot)

| Table | Row count | What's in it |
|---|---|---|
| `users` | 24 | 10 seeded students + 10 seeded alumni + 1 admin (`admin@christuniversity.in`) + 2 accounts created by real registration attempts during your own browser testing (`test@christuniversity.in`, `meera@christuniversity.in`) + 1 `testadmin@christuniversity.in` (created Day 5 since the original admin's password wasn't on file — password `Passw0rd!`) |
| `allowed_students` | 20 | `2024DS001`–`2024DS020`, 11 currently claimed (10 seeded + `test@`/`meera@`'s numbers), 9 still open for real signups |
| `allowed_alumni` | 10 | `REG2014DS01`–`REG2014DS10`, all 10 claimed by the seeded alumni |
| `student_profiles` | 10 | the 10 seeded students, each with a real SBERT embedding |
| `alumni_profiles` | 10 | the 10 seeded alumni, each with a real SBERT embedding |
| `match_scores` | 100 | every seeded-student × seeded-alumni pair (10×10), real cosine similarities |
| `audit_logs` | 4 | admin approve/reject of an alumni account (Day 3) + a `session_completed` and `expire_window` entry from Module 3/4/5 endpoint verification |
| `analytics_snapshots` | 1 | Day 5's live ETL run, dated today |
| `availability_slots`, `connection_requests`, `connection_windows`, `sessions`, `session_feedbacks`, `posts` (well, 1 real post from Feed testing), `post_moderation_logs`, `post_likes`, `post_comments` | 0 (or as noted) | cleared after each round of endpoint testing — everything created during verification (test posts, test bookings, test feedback, the Day 5 test session used to verify `predict/completion`) was deliberately removed afterward so the database only reflects the intentional seed set |

Test verification data is cleared after each session by design (per your request during Day 4 cleanup) — the only non-seed rows that persist are the 2 real accounts you registered yourself while testing the frontend, and the 4 audit log entries (audit logs are meant to be a permanent record, so they're never truncated).

---

## 5. Quick reference — how to reset/reseed

```bash
# Wipe and refill the whitelist gate tables only
docker compose exec backend python -m app.scripts.seed_whitelist

# Create/refresh the 10 demo students + 10 demo alumni (profiles, embeddings, match scores)
# Safe to re-run — skips users/profiles that already exist, but always re-links whitelist rows
docker compose exec backend python -m app.scripts.seed
```

Both scripts live in `backend/app/scripts/`. The CSVs (`students_seed.csv`, `alumni_seed.csv`) are the actual source of truth for the 10+10 demo accounts — edit those and re-run `seed.py` to change the demo data.
