# AlumniLink AI — Full Technical Walkthrough

How the whole system actually works, module by module, at the code level. Written from reading the real source, not from memory — every claim below points at a real file.

---

## 0. The request path, once, so every module below makes sense

```
React (Vite, :5173) → axios (attaches JWT) → FastAPI/uvicorn (:8000) → SQLAlchemy async → PostgreSQL+pgvector
                                                    ↓
                                              Redis (cache + Celery broker) → Celery worker (5 queues)
```

- **No nginx.** Vite's dev server serves the frontend directly; the browser calls FastAPI on a different port directly. CORS middleware (`main.py`) is what makes that legal — it's standing in for what a reverse proxy would otherwise unify.
- **Auth on almost every route** goes through one dependency chain (`core/dependencies.py`): `get_current_user` decodes the JWT → loads the `User` row → `require_student`/`require_alumni`/`require_admin` checks the role. Fails fast with 401/403 before your endpoint body runs.
- **Every DB session** comes from `get_db()` (`database.py`): opens an async session, commits if your route returns normally, rolls back on any exception, always closes. You never manually commit inside a router — you just build up changes on `db` and return.

---

## 1. Module 1 — Auth & the whitelist gate

**Files:** `routers/auth.py`, `services/auth_service.py`, `core/security.py`

**Registration** (`register_user`, `auth_service.py:26`):
1. Check the email isn't already taken.
2. Look up the submitted roll number / register number in `allowed_students` / `allowed_alumni`. Not found → `403`. Already claimed (`is_registered=True`) → `409`.
3. Students get `verification_status = verified` immediately. Alumni get `pending` — they can log in, but can't create a profile or post availability until an admin approves them.
4. Create the `User` row, hash the password with bcrypt, flush. If a race condition slips a duplicate past the whitelist check (two requests hitting the same roll number simultaneously), the DB's own unique constraint fires an `IntegrityError`, which is caught and turned into a clean `409` instead of a raw crash.
5. Flip the whitelist row's `is_registered = True` and link `registered_user_id`.
6. Issue an access token (60 min) + refresh token (7 days).

**Tokens** (`core/security.py`): both are JWTs signed with `HS256` and a shared secret. Each carries a `type` claim (`"access"` or `"refresh"`) so a refresh token can never be presented where an access token is expected — `decode_access_token` explicitly checks `type == "access"`.

**Refresh** (`refresh_access_token`): validates the refresh token, then issues a **brand new pair** (both access and refresh rotate) — so a leaked refresh token only has a shrinking window before it's superseded.

**Frontend side:** `api/axios.js` attaches the token to every request via an interceptor, and on a `401` automatically calls `/auth/refresh`, swaps tokens into `localStorage`, and retries the original request once — the user never sees a forced logout just because 60 minutes passed.

---

## 2. Module 2 — Profiles + real SBERT semantic matching

**Files:** `routers/profiles.py`, `routers/matching.py`, `services/matching_service.py`, `services/ml/embeddings.py`

**Embedding generation** (`embeddings.py`): `sentence-transformers`'s `all-MiniLM-L6-v2` model is loaded **once at process import time** (a module-level singleton) so no request pays model-load latency. `encode_text()` turns any string into a 384-float vector.

**Profile creation** (`profiles.py:58`): when a student submits their profile, the router concatenates `career_goal + skills + profile_description` into one string, embeds it, and stores the 384-dim vector directly in the `student_profiles.embedding` **pgvector column**. Alumni profiles do the same with `designation + industry + skills + about_me`. Editing a profile re-embeds from scratch.

**Matching is computed in application code, not a pgvector SQL query** — worth knowing precisely: `GET /matching/alumni` (`matching.py:26`) pulls the student's own embedding, then `get_verified_alumni_with_embeddings()` (`matching_service.py:11`) fetches **every verified alumnus with a non-null embedding** from Postgres, and the router loops over them in Python computing `cosine_similarity(student.embedding, alumni.embedding)` via plain numpy (`dot(v1,v2)/(norm(v1)*norm(v2))`), sorts descending, returns the top 20. Every pair computed also gets **upserted into `match_scores`** as a cache (`upsert_match_score`) so later lookups (predictions, single-score checks) don't recompute. At this dataset size (10-20 alumni) this is fine; pgvector's native `<->` distance operator would be the next step if the alumni pool were large enough that O(n) Python-side scoring became a bottleneck.

**`get_or_compute_match_score()`** (`matching_service.py:41`) is the shared "look up cache, else compute+cache" helper reused by both the matching router and the predictive-models router — one source of truth for "how do I get this student/alumnus pair's score."

---

## 3. Module 3 — AI outreach screening

**Files:** `routers/screener.py`, `services/ml/screener.py`

`screen_message()` is a **pure rule-based heuristic function — no ML model, no API call**. Four checks, each worth 0.25:
1. **Intent** — counts hits against a keyword list (`mentorship`, `guidance`, `career`, `schedule`, ...), capped at 3 matches for full credit.
2. **Professional tone** — starts at 0.25, subtracts 0.05 per unprofessional signal found (`hey`, `asap`, `refer me`, ...).
3. **Personalisation** — counts phrases like "your experience", "your company" — did the student actually reference *this* alumnus, not send a form letter.
4. **Message quality** — word count: ≥50 words = full credit, ≥30 = partial, <30 = zero.

Sum ≥ **0.6** = pass. The response also includes per-dimension `breakdown` and actionable `suggestions` for whichever dimensions scored low — this is what powers the live "type and watch your score update" UX on the Send Request page (`POST /screener/check` is a preview-only endpoint that doesn't save anything).

The **real gate** is inside `POST /requests/` (`requests.py:55`): the same `screen_message()` runs server-side (never trust the client's preview score) and a sub-0.6 message gets rejected with `400` before a `ConnectionRequest` row is even created.

---

## 4. Module 4 — 48-hour connection window & concurrency-safe booking

**Files:** `routers/requests.py` (accept), `routers/sessions.py` (book), `core/redis_client.py`, `main.py` (listener), `workers/tasks.py` (`expire_window`)

**On accept** (`requests.py:152`, `PATCH /requests/{id}/accept`):
1. Flip the request to `accepted`.
2. Create a `ConnectionWindow` row: `expires_at = now + 48h`, `status = active`.
3. Link it back onto the request (`req.window_id`).
4. **`set_window_ttl(window.id, 48*3600)`** — sets a Redis key `window:{id}` with a real 48-hour TTL.

**The expiry mechanism, precisely** (this is the most "distributed systems" part of the project): Redis doesn't push a webhook when a key expires — you have to *ask* for that via **keyspace notifications**. At startup, `main.py`'s `lifespan` runs `redis_client.config_set("notify-keyspace-events", "Ex")` and spawns a background `asyncio` task that `psubscribe`s to `__keyevent@0__:expired`. When `window:{id}`'s TTL lapses, Redis publishes the bare key name on that channel; the listener catches it, and calls `expire_window.delay(id)` — **handing off to Celery**, not doing the DB write itself (the FastAPI process shouldn't own that transaction). `expire_window` (in `workers/tasks.py`) then flips the window to `expired`, flips its linked request to `expired` too, and writes an `audit_logs` row with `actor_id = None` (nobody clicked anything — the system did it).

**On booking** (`sessions.py:30`, `POST /sessions/book`): checks the window is still `active` and not past `expires_at`, then does the important part —

```python
select(AvailabilitySlot).where(...).with_for_update()
```

a **Postgres row lock**. If two requests try to book the same slot at the same instant, the second one blocks until the first's transaction commits, then sees `slot.status == booked` and gets a clean `409` instead of both succeeding. This was proven under an actual concurrency test, not just reasoned about. On success: slot → `booked`, window → `booked`, a `Session` row is created (its `scheduled_at`/`duration_minutes` derived from the slot's date/start/end time), and `clear_window_ttl()` deletes the Redis key so the expiry listener never fires for a window that was actually used.

---

## 5. Module 9 — Availability slots

**Files:** `routers/availability.py`

Straightforward CRUD scoped to the calling alumnus's own `AlumniProfile.id`, gated by `verification_status == verified` on creation. The one rule worth remembering: **a slot with `status != open` (i.e. already booked) cannot be edited or deleted** — both `update_slot` and `delete_slot` check this and return `400` if violated, so a student's booked session can't be silently pulled out from under them.

---

## 6. Session lifecycle & feedback

**Files:** `routers/sessions.py`

- `PATCH /sessions/{id}/complete` — **alumni-only**, only works on a `scheduled` session, flips it to `completed`, writes an `audit_logs` row.
- `POST /sessions/{id}/feedback` — **student-only**, only works on a `completed` session, rejects a second submission from the same reviewer (`400`), validates rating is 1–5.
- `GET /sessions/{id}/feedback` — either participant can read it back; the endpoint resolves both the session's student and alumnus back to their `users.id` and checks the caller is one of them before returning anything.

---

## 7. Module 5 — Community feed & 4-layer moderation

**Files:** `routers/feed.py`, `services/ml/moderation.py`, `routers/admin.py` (moderation_router)

**`moderate_post()`** (`moderation.py:30`) runs in strict order, short-circuiting on the first failure:
1. **Length** — under 5 words → hard reject.
2. **Spam keywords** — ≥2 hits from a list (`"click here"`, `"guaranteed"`, `"buy now"`, ...) → hard reject.
3. **Toxicity** — runs the content through `unitary/toxic-bert` (loaded via `transformers.pipeline("text-classification", ...)`, a **lazy-loaded singleton**, same pattern as the SBERT model). Score > 0.7 → hard reject.
4. **Borderline** — 0.4 < score ≤ 0.7 → not rejected, but flagged `pending_review` for an admin to decide.
5. Anything under 0.4 → `approved` outright.

This replaced the originally-spec'd `detoxify` library, which turned out to be a genuine dead end (its dependency pins are incompatible with what SBERT needs — see §11). `unitary/toxic-bert` is the real thing running, wrapped in a `try/except` that falls back to `toxicity=0.0` only if the model genuinely can't load in this environment (never silently on a real toxic string).

**Creating a post** (`feed.py:50`): runs `moderate_post()`, sets `moderation_status` accordingly, and — this is a subtlety worth knowing — **even a hard-rejected post is persisted** (post row + a `post_moderation_logs` row) before the `400` is raised back to the author, specifically so there's an audit trail of what got rejected and why, even though the author only sees an error.

**Likes**: `post_likes` has a **unique DB constraint on `(post_id, user_id)`**, not just app-level logic — `toggle_like` checks for an existing row and deletes-or-inserts, so "can't double-like" is enforced at two layers.

**Comments**: also run through `moderate_post()` before saving — same pipeline, same thresholds.

**Admin moderation queue** (`admin.py`'s `moderation_router`, mounted at `/api/v1/admin/moderation`): `GET /queue` lists everything sitting in `pending_review`; `PATCH /{id}/approve` or `/reject` resolves it and logs the decision (with `moderator_id`) to `post_moderation_logs`.

---

## 8. Module 6 — Predictive models (real trained ML)

**Files:** `services/ml/predict.py`, `routers/predict.py`, `scripts/train_models.py` (training, run at Docker build time)

Two actual scikit-learn models, trained offline and shipped as `.pkl` files loaded lazily (module-level singletons, same pattern as everything else ML in this project):

- **Response-likelihood model**: `LogisticRegression` + `StandardScaler`, features = `[screening_score, match_score, experience_years]`. `GET /predict/response/{alumni_id}` pulls the student's cached match score (or computes it fresh via `get_or_compute_match_score`), their most recent request's screening score (or a `0.7` default if they haven't sent one yet), and the target alumnus's `experience_years`, scales the feature vector, and returns `predict_proba(...)[0][1]` — the probability of class "1" (got a response).
- **Completion-likelihood model**: `RandomForestClassifier`, features = `[match_score, screening_score, experience_years, session_hour]`. `GET /predict/completion/{session_id}` — participant-only (checked against both the student's and alumnus's `users.id`) — pulls the same signals plus the booked slot's start hour.

Both return a float **and** a human label via `interpret()`: >0.7 = "High", ≥0.4 = "Medium", else "Low". This is exactly what renders as the prediction badge on the Alumni Profile page.

**Honest caveat, worth stating out loud in the presentation**: these models are trained on ~30 synthetic/illustrative rows in `train_models.py`, not real historical platform outcomes — there isn't enough usage history yet. The predictions are directionally reasonable, not calibrated probabilities.

---

## 9. Module 7 — Admin analytics (bronze → silver → gold ETL)

**Files:** `services/analytics_service.py`, `routers/admin.py`, `workers/tasks.py` (`run_nightly_etl`)

`compute_metrics()` (`analytics_service.py:13`) is the whole pipeline in one function:
- **Bronze** — raw `COUNT`/`AVG` queries straight off the tables: student/alumni counts, pending alumni, request counts by status, session counts, completed sessions, approved posts, average rating, average cosine match score, average screening score.
- **Silver** — derived on top of bronze in the same dict: `acceptance_rate = accepted/total_requests`, `completion_rate = completed/accepted`, `avg_match_score_pct`.
- **Gold** — `save_snapshot()` upserts the combined dict as a JSONB blob into `analytics_snapshots`, keyed by `snapshot_date` (one row per calendar day; re-running same-day updates in place rather than duplicating).

`GET /admin/analytics/summary` runs this **inline, live**, every time it's called (also saving a snapshot as a side effect). `GET /admin/analytics/snapshots` returns the last 30 days for trend charts. Separately, **Celery Beat** (configured in `celery_app.py`'s `beat_schedule`, `crontab(hour=2, minute=0)`) fires `run_nightly_etl` automatically every night — same underlying function, scheduled rather than on-demand.

---

## 10. Module 10 — Request-scoped chat messaging

**Files:** `routers/messages.py`, `models/message.py`, `components/chat/ChatThread.jsx`

Deliberately **not** tied to a session — tied to the `connection_request`. `_get_request_as_participant()` (`messages.py:17`) is the single guard both endpoints share: resolves the request's student/alumnus back to `users.id`, checks the caller is one of them (`403` otherwise), and checks `req.status == accepted` (`403` on pending/rejected/withdrawn/expired). Because this project's `RequestStatus` enum has no `completed` state — booking and session-completion never touch `connection_requests.status` — a request that was accepted **stays accepted forever**, which is exactly what lets the same thread stay open through slot booking and session completion with zero extra logic keyed off `session_id`.

Frontend polls `GET /requests/{id}/messages` every 7 seconds (`ChatThread.jsx`) — deliberately no websockets, kept simple by design.

---

## 11. Background jobs — what Celery is actually doing

**Files:** `workers/celery_app.py`, `workers/tasks.py`

One worker container, **5 named queues** (`celery, screening, windows, reminders, analytics`), routed explicitly by task name (`task_routes` in `celery_app.py`) — this mattered because early on the worker only consumed the default `celery` queue and tasks routed elsewhere silently never ran (a real bug hit and fixed, see PROGRESS.md Day 4).

Four registered tasks:
- `expire_window` — fired by the Redis pub/sub bridge, not on a schedule (§4 above).
- `run_nightly_etl` — fired by Celery Beat, 2am daily (§9 above).
- `send_session_reminder` — **currently a stub / placeholder**, no email/notification layer exists yet.
- `screen_alumni_profile_task` — wraps the (separate, admin-facing) alumni-profile quality screener.

---

## 12. Admin layer (cuts across everything)

**Files:** `routers/admin.py`

- **Alumni verification**: `GET /admin/alumni/pending`, `POST /admin/alumni/{id}/approve|reject` — this is the gate that flips `verification_status` from `pending` to `verified`, unlocking profile creation and availability posting for that alumnus (Modules 2 & 9's actual enforcement point).
- **User management**: `GET /admin/users` (role filter), `PATCH /admin/users/{id}/ban`.
- **Audit logs**: `GET /admin/audit-logs` (action filter) — every admin action and every system-triggered event (`expire_window`, `session_completed`) writes here.
- **Analytics/Reports**: covered in §9.
- **Moderation queue**: covered in §7.

Every admin mutation writes an `AuditLog` row with `actor_id = current_user.id` — the only exception is `expire_window`, which is system-triggered and correctly logs `actor_id = None`.

---

## 13. "Are we using LLMs?" — direct answer: no, and here's exactly what runs instead

**No OpenAI, no Anthropic/Claude, no GPT, no API-based LLM call exists anywhere in this codebase** — confirmed by grep across the entire backend, not an assumption. If asked "did you use ChatGPT/an LLM to power this," the honest, precise answer is: **no LLM inference happens at runtime at all.** What actually runs, all of it **local, open-source, loaded once per process, zero external API calls at request time**:

| "AI" feature | What's actually running | Type of model |
|---|---|---|
| Alumni matching (Module 2) | `sentence-transformers`, `all-MiniLM-L6-v2` | Pretrained SBERT embedding model (encoder-only transformer, ~22M params) — downloaded once from Hugging Face Hub, then runs 100% locally |
| Toxicity detection (Module 5) | `unitary/toxic-bert` via `transformers.pipeline` | Pretrained BERT fine-tuned for toxicity classification — also local, also from Hugging Face Hub |
| Outreach message screening (Module 3) | `screen_message()` in `services/ml/screener.py` | **Not a model at all** — hand-written keyword/heuristic scoring function |
| Spam/length checks (Module 5, layers 1–2) | `moderate_post()` | Also plain rule-based code, no model |
| Response/completion prediction (Module 6) | `LogisticRegression` + `RandomForestClassifier` (scikit-learn) | Classic, small, trained-in-house ML — not a language model at all |

**Why this distinction matters for your presentation**: "AI-powered matching" is true and defensible — SBERT is a real, published, widely-used transformer model doing real semantic embedding, not a keyword match. But it is not a chatbot, not text-generation, and nothing is "asking an LLM" to score a message or moderate a post — those are deterministic functions you can point to and read line-by-line (§3 and §7 above). If someone asks "which LLM," the accurate answer is "none — we use two open-source classification/embedding transformers (SBERT, toxic-bert) that run locally, plus two classic scikit-learn models," not a made-up brand name.

One necessary caveat: the SBERT and toxic-bert model *weights* are downloaded from Hugging Face Hub the first time each container runs (cached afterward) — so there is an internet dependency the first time, but no live API call, no per-request network round-trip, and no cost per inference. Everything after that first download is fully offline.

---

## 14. Seed data — exactly where every row in the demo database comes from


**Files:** `scripts/seed_whitelist.py`, `scripts/seed.py`, plus 4 CSVs sitting next to them in `backend/app/scripts/`: `students_seed.csv` (20 rows), `alumni_seed.csv` (10 rows), `connection_requests_seed.csv` (30 rows), `sessions_seed.csv` (20 rows).

Nothing in the database is hardcoded into Python logic — every seeded row is inserted by a script you run yourself, reading from a CSV, using the exact same models and services the live API uses (same `hash_password()`, same `encode_text()` SBERT call, same `upsert_match_score()`). Two separate scripts, run in order:

### Step 1 — `seed_whitelist.py` (the registration gate)
Generates `2024DS001`–`2024DS020` (20 student roll numbers) and `REG2014DS01`–`REG2014DS10` (10 alumni register numbers) directly in code (not from a CSV — these are just sequential IDs), **deletes every existing row in `allowed_students`/`allowed_alumni` and reinserts fresh** each time it's run. This is intentionally destructive-but-safe: it only resets the *gate* table, never touches `users` or any real registered account, so re-running it doesn't affect anyone who already signed up.

### Step 2 — `seed.py` (the actual pilot dataset), run as one `seed()` function, in this exact order:

1. **`_seed_students()`** — reads `students_seed.csv` (columns: `email, password, full_name, roll_number, department, degree, graduation_year, career_goal, skills, profile_description`). For each row: if a `User` with that email doesn't already exist, creates one (`hash_password()` on the plaintext seed password, `verification_status=verified` immediately since students need no admin gate); marks the matching whitelist row `is_registered=True`; if a `StudentProfile` doesn't already exist, builds the embedding text (`career_goal + skills + profile_description`), calls the **real `encode_text()`** (the actual SBERT model, no shortcut), and creates the profile. Returns a `{roll_number: StudentProfile}` dict for later steps to key off of.
2. **`_seed_alumni()`** — identical pattern from `alumni_seed.csv` (columns: `..., register_number, company, designation, industry, experience_years, skills, about_me`), except alumni get `verification_status=verified` too (the seed script pre-verifies them so the demo doesn't require manually approving 10 accounts before matching works).
3. **`_seed_match_scores()`** — the double loop: every one of the 20 students × every one of the 10 alumni, **real `cosine_similarity()` on their real stored embeddings** (not fake numbers), upserted via the same `upsert_match_score()` the live matching endpoint uses. 200 rows.
4. **`_seed_requests()`** — reads `connection_requests_seed.csv` (columns: `ref, student_roll_number, alumni_register_number, message, screening_score, outcome`). `outcome=PASS` → `ConnectionRequest.status=accepted` (and a matching `ConnectionWindow` is created, pre-set to `status=booked` since these are historical/already-resolved, not live 48h countdowns); `outcome=FAIL` → `status=rejected`. Keyed by roll number / register number, not raw database IDs, so the CSV stays human-editable without knowing internal primary keys.
5. **`_seed_sessions()`** — reads `sessions_seed.csv` (columns: `ref, request_ref, scheduled_at, duration_minutes, status`), where `status` is `completed`/`upcoming`/`cancelled` (mapped to the real `SessionStatus` enum's `completed`/`scheduled`/`cancelled` — the CSV's friendlier label doesn't match the enum name 1:1, `SESSION_STATUS_MAP` bridges it). For each row, also fabricates a matching `AvailabilitySlot` (marked `booked`, so the data is structurally consistent with what a real booking flow would have produced — not a bare orphaned session row) and, for every `completed` session, a `SessionFeedback` with a random 4-or-5 rating.
6. **`_seed_posts()`** — **not from a CSV** — 5 posts hardcoded directly in the script (`SAMPLE_POSTS`), one per `post_type`, distributed across 4 alumni + 1 student author.
7. **`_seed_messages()`** — also hardcoded (`SAMPLE_MESSAGE_THREAD`/`SAMPLE_MESSAGE_CONTENT`) — drops a 3-message back-and-forth onto the first 3 already-accepted seeded requests, purely for demo purposes.

**Idempotency, precisely**: every step checks "does this already exist?" (by email, by student+alumnus pair, by request_id, by post content, etc.) before inserting — so running `python -m app.scripts.seed` a second time against an already-seeded database is a safe no-op, not a duplicate-data bug. This is what let the project be re-seeded fresh on a second machine (Day 8) without any manual cleanup.

**The one genuinely hardcoded thing in the whole system** is the *shape* of the whitelist gate itself (§1) — not the demo people, the mechanism. Every account, profile, request, session, and score you'll see in the demo is a real row a real script inserted through real model/service code — nothing is faked or mocked to just "look right" in the UI.

---

## 15. Why there's no nginx, no gunicorn, no production hardening — and that's fine to say

This is a Docker Compose **dev-mode** stack: `uvicorn --reload` (single process, auto-reloads on file change) and `npm run dev` (Vite's dev server), not a production build (`npm run build` → static `dist/` served behind a real reverse proxy with TLS, gzip, and multiple uvicorn/gunicorn workers). That's a legitimate, standard way to build and demo a pilot project — just be upfront if asked "would you deploy this as-is": no, this is the development topology, and going to production would mean adding a reverse proxy, building the frontend statically, running multiple backend workers, and moving secrets out of `docker-compose.yml`'s defaults.