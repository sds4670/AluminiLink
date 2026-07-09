# AlumniLink AI — Progress & Database Guide

This file explains, in plain language: what's been built so far (day by day), and exactly how the database works right now — what's real, what's seeded, and what's hardcoded.

Last updated: 2026-07-09

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

14 tables total. Grouped by what they're for.

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

### 3.3 Availability & booking (Module 9 + future session booking)

**`availability_slots`**
| Column | Type | Notes |
|---|---|---|
| `id` | int, PK | |
| `alumni_id` | int, FK → `alumni_profiles.id` | |
| `slot_date` | date | |
| `start_time` / `end_time` | time (no timezone) | |
| `status` | enum `slotstatus` | current code only ever writes `open` or `booked`. The enum type in Postgres *also* still contains the old `available`/`cancelled` values from an earlier design (added, never removed) — they simply go unused. |
| `created_at` | timestamp | |

**`connection_windows`** — a bulk time-window an alumnus opens for requests (separate, older mechanism from a different module, not part of what we built this session — pre-existed in the Day 1 scaffold).

**`connection_requests`** — a student's request to connect with an alumnus.
| Column | Type | Notes |
|---|---|---|
| `student_id` / `alumni_id` | FK → `student_profiles.id` / `alumni_profiles.id` | |
| `window_id` | FK → `connection_windows.id`, nullable | |
| `status` | enum `requeststatus` | `pending`/`accepted`/`rejected`/`withdrawn`/`expired` |
| `message` / `rejection_reason` | text | |

**`sessions`** — a scheduled 1:1 mentoring session (booking logic itself isn't built yet — this table exists from Day 1 scaffold, referenced by `availability_slots.id` via `slot_id`, but nothing currently sets `slot.status = booked` automatically).

**`session_feedbacks`** — post-session rating (1–5) left by either party.

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

### 3.5 Content & moderation (Feed module — pre-existing, not touched this session)
**`posts`**, **`post_moderation_logs`** — a student/alumni feed with (stubbed) auto-moderation.

### 3.6 Admin
**`audit_logs`** — records admin actions (`approve_alumni`, `reject_alumni`, `ban_user`, etc.) with who did it and when.

---

## 4. What's actually in the database right now (snapshot)

| Table | Row count | What's in it |
|---|---|---|
| `users` | 23 | 10 seeded students + 10 seeded alumni + 1 admin (`admin@christuniversity.in`) + 2 accounts created by real registration attempts during your own browser testing (`test@christuniversity.in`, `meera@christuniversity.in`) |
| `allowed_students` | 20 | `2024DS001`–`2024DS020`, 11 currently claimed (10 seeded + `test@`/`meera@`'s numbers), 9 still open for real signups |
| `allowed_alumni` | 10 | `REG2014DS01`–`REG2014DS10`, all 10 claimed by the seeded alumni |
| `student_profiles` | 10 | the 10 seeded students, each with a real SBERT embedding |
| `alumni_profiles` | 10 | the 10 seeded alumni, each with a real SBERT embedding |
| `availability_slots` | 1 | one leftover slot from testing (status `booked`) |
| `match_scores` | 100 | every seeded-student × seeded-alumni pair (10×10), real cosine similarities |
| `audit_logs` | 2 | one alumni approval + one alumni rejection, both done during testing |
| `connection_requests`, `connection_windows`, `sessions`, `session_feedbacks`, `posts`, `post_moderation_logs` | 0 | untouched — no module has exercised these yet in a way that left data behind |

If you want a completely clean slate for a demo, the two extra accounts (`test@christuniversity.in`, `meera@christuniversity.in`) and the one leftover slot are the only things not part of the intentional seed set.

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
