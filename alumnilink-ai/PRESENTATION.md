# AlumniLink AI — Presentation Guide

A university alumni mentorship platform with real AI-powered matching, screening, and moderation. Use this as your script: what to say, what to click, and what to say if someone asks a hard question.

---

## 0. USP — what to actually say when asked "why is this different from LinkedIn"

**One-line pitch**: *"AlumniLink AI turns alumni mentorship from a cold LinkedIn DM into a structured, AI-matched, time-bound program — with message-quality screening that protects mentors' time, a 48-hour window that forces action instead of letting conversations die, and full-lifecycle analytics that actually tell the university whether mentorship is working."*

**The six things that are genuinely differentiated, not just "we built a website":**

1. **Real semantic matching, not keyword search.** SBERT embeddings + cosine similarity, not "search by company name." Nobody browsing LinkedIn gets a computed 67% match score against their own stated career goals.
2. **Structured urgency.** The 48-hour booking window is the single most distinctive mechanic here — it's the difference between "a mentor said yes" and "a mentor said yes AND a real session got scheduled." Nothing about LinkedIn/email/WhatsApp forces that.
3. **Outreach is quality-gated before it reaches a mentor.** Alumni time is the scarcest resource in any mentorship program — the 4-dimension screener exists specifically to protect that, so alumni don't get burned out by "hi can u refer me" messages and quietly stop responding.
4. **One platform, full lifecycle.** Discovery → screening → request → accept → book → meet → complete → feedback → analytics, in one system with one login — not fragmented across LinkedIn + Calendly + WhatsApp + a Google Form the alumni office forgets to check.
5. **Institutional accountability.** The admin analytics (acceptance rate, completion rate, avg match quality) is something a university can actually use to justify or improve the program — manual/LinkedIn-based mentorship gives an institution zero visibility into whether it's working.
6. **A real trust layer.** Whitelist-gated registration (roll/register number checked against the official roster) plus admin-reviewed alumni profiles means a student knows they're talking to a verified, real person from their own university — not an open network of strangers.

**If asked "so what's actually AI here, not just a web app"** — see §16 below; be precise, not hand-wavy.

### What gets each user type in the door, vs. what makes them come back

Getting a signup and keeping someone active are different problems — worth separating explicitly if asked "how do you attract and retain users":

**Students — attracted by:** a real, personalized match score on Browse Alumni (not a generic directory), and the promise of an actual conversation, not a black hole.
**Students — retained by:**
- The screener's live feedback while typing teaches them to write better outreach — a skill they keep using, not a one-time gate.
- The 48-hour window creates a fast gratification loop: sign up → matched → screened → accepted → booked, in days, not the weeks/silence typical of cold LinkedIn outreach.
- The community feed gives them a reason to open the app even between mentorship cycles (jobs, internships, resources from alumni).
- Follow-up sessions with the same mentor are now explicitly supported after a session completes (not a dead end) — encourages an ongoing relationship, not one-and-done.

**Alumni — attracted by:** a low-friction way to give back (post availability once, optionally share jobs/resources) without their inbox becoming a chore.
**Alumni — retained by:**
- Message screening is the actual retention mechanic here — it's the single biggest real-world cause of mentor burnout ("hi can u get me a referral" spam) and this platform structurally prevents it from reaching them at all.
- Mentor tier badges (Bronze → Elite) + the AI Mentor Score gamify contribution — visible status for something that's otherwise thankless and invisible.
- The feed lets them post their own company's openings — this isn't just altruism, it's a genuine sourcing channel from their own alma mater, so the platform gives back to them too.

**The institution (the actual decision-maker/"client")— attracted by:** solving a real, named problem (unmeasurable, ad-hoc alumni engagement) rather than a generic feature list.
**Institution — retained by:**
- Real analytics (acceptance rate, completion rate, match quality trend) — the thing that lets an alumni relations office actually prove program ROI to leadership, which most manual/LinkedIn-based programs can never do.
- Moderation is largely automated (4-layer pipeline) — low ongoing operational burden, not a new full-time job for staff.
- Whitelist-based onboarding scales to any class size with zero extra admin work per student.

---

## 1. The one-liner

**AlumniLink AI connects students with alumni mentors using real semantic matching (SBERT embeddings), then runs the entire mentorship lifecycle end-to-end** — outreach screening → connection request → 48-hour booking window → session → feedback → chat — with an admin layer for verification, moderation, and analytics on top.

10 modules, 16 database tables, ~30 API endpoints, 29 frontend pages, a full Docker stack (FastAPI + PostgreSQL/pgvector + Redis + Celery + React), 12 passing integration tests, 65 documented test cases.

---

## 2. Tech stack (say this to establish credibility fast)

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python 3.11), fully async | high-performance async I/O, auto-generated OpenAPI docs |
| Database | PostgreSQL 15 + **pgvector** | native vector similarity search for embeddings, not a bolted-on vector DB |
| ORM | SQLAlchemy 2 (async) | |
| Queue / background jobs | Celery + Redis 7 | 48-hour window expiry, nightly analytics ETL, session reminders |
| ML | `sentence-transformers` (SBERT, `all-MiniLM-L6-v2`), scikit-learn, `unitary/toxic-bert` | real embeddings + real trained models, not mocks |
| Frontend | React 18 + Vite + Tailwind CSS + Recharts | |
| Auth | JWT (access + refresh tokens), bcrypt | |
| Infra | Docker Compose, 5 services (backend, frontend, postgres, redis, celery worker) | one-command spin-up |

**Talking point:** everything runs in Docker Compose — `docker compose up --build` — five coordinated services, not a single monolith script.

---

## 3. Architecture at a glance

```
React (Vite) ──HTTP/JWT──▶ FastAPI ──async──▶ PostgreSQL + pgvector
                               │
                               ├──▶ Redis (cache, pub/sub key-expiry, Celery broker)
                               └──▶ Celery worker (5 queues: celery, screening,
                                     windows, reminders, analytics)
```

- **10 routers** (`backend/app/routers/`): auth, profiles, matching, screener, requests, windows, sessions, availability, feed, messages, admin, predict
- **16 tables**, all created from SQLAlchemy models (`backend/app/models/`) — nothing hardcoded in Python; every row got there via a seed script, a real API call, or (rarely) manual SQL. See §7 for the full schema story.
- **Role-based access**: `student` / `alumni` / `admin`, enforced via FastAPI dependencies (`require_student`, `require_alumni`, `require_admin`) on nearly every endpoint.

---

## 4. Walk through the 10 modules (this is the core of your talk)

Present these roughly in the order a real user would hit them.

### Module 1 — Authentication & the whitelist gate
- `POST /auth/register`, `/login`, `/refresh`, `GET /me`.
- **Whitelist gate**: you can only register if your roll number (student) or register number (alumni) is already sitting in the `allowed_students` / `allowed_alumni` table — modeling "only people the university actually enrolled/employed can make an account." Think of it as a guest list: names on the list aren't accounts until someone registers with that exact number.
- Passwords hashed with bcrypt; JWT access token (60 min) + refresh token (7 days), each carrying a `type` claim so one can't be replayed as the other.
- Alumni can log in immediately, but a `verification_status` flag (`pending → verified/rejected`, set by an admin) gates whether they can build a profile or post availability — not login itself.

### Module 2 — Profiles + real SBERT semantic matching
- Students fill in department/degree/career goal/skills; alumni fill in company/designation/industry/skills.
- **Every profile gets a genuine 384-dimension SBERT embedding** (`sentence-transformers`, `all-MiniLM-L6-v2`) computed from their text fields, stored in a **pgvector** column.
- Matching (`GET /matching/alumni`) is real **cosine similarity** search over those embeddings — not a keyword match, not a random stub.
- `match_scores` acts as an upsert cache: recomputed and overwritten every time a student browses alumni.

### Module 3 — AI outreach screening
- Before a student can send a connection request, their message is scored on 4 dimensions — intent, professional tone, personalisation, length — by `screen_message()`.
- Score must be **≥ 0.6** to submit. `POST /screener/check` lets the frontend preview the score live before submitting (visible in the "Send Request" page as the score updates while typing).
- Real example from testing: a generic message scored 0.25 (fail); a personalized one scored 0.85 (pass).

### Module 4 — The 48-hour booking window
- When an alumnus accepts a request, a `connection_window` opens with a hard **48-hour expiry**.
- The student must book one of the alumnus's open availability slots inside that window, or it auto-expires.
- **Real Redis TTL**: a `window:{id}` key is set with a 48h TTL; a background listener subscribes to Redis's key-expiry pub/sub channel and fires a Celery task (`expire_window`) the instant it lapses — verified end-to-end with short-TTL test keys.
- **Concurrency-safe booking**: uses a Postgres row lock (`SELECT ... FOR UPDATE`) so two simultaneous booking attempts on the same slot can't both succeed. Proven under a real concurrency test — one request gets `201`, the other a clean `409`.

### Module 9 — Availability slots
- Alumni post/edit/delete "I'm free at this time" slots. Students browse an alumnus's open slots when booking. Booked slots can't be edited or deleted.

### Session lifecycle & feedback
- `PATCH /sessions/{id}/complete` (alumni-only, logged to `audit_logs`) closes the loop: book → alumni marks complete → student leaves a 1–5 star rating (duplicate feedback and wrong-status both guarded) → either participant can read it back.

### Module 5 — Community feed + 4-layer moderation
- 7 post types: internship / job / event / resource / query / announcement / general.
- **4-layer moderation pipeline** (`moderate_post()`): length check → spam-keyword check → toxicity check → borderline-toxicity admin review.
- Toxicity is powered by `unitary/toxic-bert` (loaded via `transformers`, already installed for SBERT) — a real toxic string scored 0.987 and was hard-rejected; a normal post scored 0.001 and was approved.
- Posts, likes (toggle, unique-constrained at the DB level), and comments (also moderated) all live under `/feed/...`. Borderline cases land in an admin moderation queue.

### Module 6 — Predictive models (real trained ML, not stubs)
- Two scikit-learn models, trained in `train_models.py`, persisted with `joblib`:
  - `LogisticRegression` (+ `StandardScaler`) — likelihood a student's outreach gets a response.
  - `RandomForestClassifier` — likelihood a booked session actually completes.
- `GET /predict/response/{alumni_id}` and `GET /predict/completion/{session_id}` return a likelihood float plus a High/Medium/Low interpretation. Shown live on the Alumni Profile page as a prediction badge.
- Verified live: 0.94 → "High" on a real test case.

### Module 7 — Admin analytics (bronze → silver → gold ETL)
- **Bronze**: raw counts (students, alumni, requests, sessions, posts, avg ratings/scores).
- **Silver**: derived rates (acceptance rate, completion rate, avg-match-score %).
- **Gold**: combined dict upserted into `analytics_snapshots`, keyed by date.
- `GET /admin/analytics/summary` computes live; `GET /admin/analytics/snapshots` returns 30 days of history for trend charts (Recharts). A Celery Beat job runs this automatically every night at 2am.
- Admin Dashboard: 6 KPI cards + a funnel bar chart. Reports page: line chart of the 3 rates over time.

### Module 10 — Request-scoped chat messaging (newest module)
- A lightweight chat thread tied to a **connection request**, not a session — opens the moment an alumnus accepts, and the *same* thread persists through slot booking and session completion (one conversation per mentorship relationship).
- `POST` / `GET /requests/{id}/messages`, guarded so only the two participants on an **accepted** request can read/write.
- Frontend polls every 7 seconds (no websockets, by design) — wired into "My Requests" (student) and "My Students" (alumni).

### Admin capabilities (cuts across modules)
- Alumni approval queue (verify/reject pending alumni).
- User management (role/status filters), audit logs (action filters).
- Moderation queue for borderline posts.
- Full analytics/reports suite.

---

## 16. AI components — precisely what's real, and what's actually left to do

Be exact here, not hand-wavy — this is the question most likely to get a real cross-examination.

### What's actually running today (in order of "how much real ML is in it")

| Component | Type | Real or stub? |
|---|---|---|
| **SBERT matching** (Module 2) | Pretrained transformer embedding model (`all-MiniLM-L6-v2`), real cosine similarity | **Real.** Every match score is a genuine computation on real embeddings. |
| **Toxicity moderation** (Module 5) | Pretrained transformer classifier (`unitary/toxic-bert`) | **Real.** Verified live: toxic text scores 0.98+ and gets hard-rejected; clean text scores ~0.001. |
| **Response/completion prediction** (Module 6) | Two classic scikit-learn models (`LogisticRegression`, `RandomForestClassifier`) | **Real model, weak data.** The models genuinely run inference — but they're trained on ~30 synthetic/illustrative rows, not real platform history. Directionally reasonable, not calibrated probabilities. Be upfront about this if asked. |
| **Message screener** (Module 3) | Hand-written rule/keyword scoring function | **Not a model at all.** No embeddings, no training, just weighted keyword/word-count logic. Honest to call this "automated scoring," not "AI," if pressed on terminology. |
| **"Why recommended" explanations** (Browse Alumni cards) | — | **Not real — a hardcoded, identical list shown for every single match**, regardless of the actual pair. This is a known, honest gap (see roadmap below), not something to claim is personalized. |

**No LLM (GPT/Claude/etc.) is used anywhere** — confirmed by grep across the entire backend. If asked "which LLM," the honest answer is none; the "AI" here is two pretrained transformer models doing embedding/classification, plus classic ML, all running locally with zero API calls.

### Roadmap — what would genuinely make this stronger, in priority order

1. **Make "why recommended" real.** Right now it's a static list. The fix is straightforward given what already exists: derive the actual overlapping skills/keywords between the student's and alumnus's embedding source text and surface those, instead of a canned list — turns a fake explanation into a genuinely explainable match.
2. **Retrain the predictive models on real usage data** once enough sessions/requests have accumulated — the architecture is already correct, only the training data is synthetic.
3. **LLM-assisted message drafting.** The screener already tells a student *why* their message scored low ("add a specific ask," "reference their background") — the natural next step is generating a suggested rewrite, not just a critique. This is the one place an actual LLM would add real value here.
4. **Smarter feed moderation beyond toxicity** — spam/duplicate-content detection across posts, not just per-post keyword/toxicity checks.
5. **A lightweight recommendation/nudge layer** — e.g. surfacing "alumni who respond well to messages like yours" using the same response-likelihood model, proactively rather than only on-demand per-profile.

---

## 5. Database: is it hardcoded? (a strong point to make proactively)

**No — nothing is baked into the code.** Every row in every table got there one of three ways:
1. **Seed scripts** you run yourself (`seed_whitelist.py`, `seed.py`) — read from CSVs, insert rows, safe to re-run (idempotent, skip-if-exists).
2. **Real API calls** — anyone hitting `/auth/register` with a valid whitelist number creates a genuine account.
3. **Manual SQL**, rarely — e.g. promoting the first admin account.

The **only** intentionally hardcoded thing is the whitelist *mechanism itself* — the gate, not the accounts behind it.

**Current pilot dataset** (demo-ready): 20 students, 10 alumni, 200 precomputed match scores, 30 connection requests (20 accepted / 10 rejected), 20 sessions (15 completed / 4 upcoming / 1 cancelled), 15 feedback ratings, 5 feed posts, a 3-message sample chat thread on 3 accepted requests.

---

## 6. Quality & testing (have this ready if asked "how do you know it works?")

- **12 integration tests** (`backend/tests/test_integration.py`), run against the *real* live stack (backend + Postgres + Redis), not a mocked ASGI app. Each test creates its own throwaway user and cleans up after itself. All pass.
- **65 documented test cases** (`docs/test_cases.md`) across all 9 original modules, each mapped to either the automated suite or a live verification pass.
- **Pre-presentation smoke test** (Day 8): all 10 core flows re-verified live — login/JWT, real non-zero match scores (e.g. 0.67), screener pass/fail, prediction badges, availability booking, admin analytics matching real DB counts, `/health` reporting the SBERT model as loaded, and all 4 key frontend pages screenshotted with zero console errors and real data rendering.
- **`/health` endpoint** distinguishes "process is up" from "ML model actually loaded."

---

## 7. Honest known limitations (own these — it reads as rigor, not weakness)

- **Predictive models train on synthetic data.** ~30 illustrative rows, not real historical outcomes yet (not enough usage history exists). Predictions are directionally reasonable, not calibrated probabilities.
- **Single department only** (Data Science) in the current pilot dataset — the schema itself has no department dimension yet, so multi-department matching hasn't been exercised.
- **No email/SMS notifications** — request acceptance, window-expiry, reminders all happen in-app only. Deferred.
- **No calendar integration** — sessions use a plain timestamp, no `.ics` export or calendar sync. Deferred.
- **`detoxify` (the originally-spec'd library) couldn't be installed** — a genuine, unresolvable dependency conflict (it hard-pins `transformers==4.22.1`, which conflicts with the version SBERT needs; the resulting downgrade path needs a newer Rust compiler than the container's Debian ships). **Fixed properly, not worked around**: swapped to `unitary/toxic-bert`, the same underlying architecture, loaded directly via the `transformers` library already installed — fully live, not a stub.

If asked "what would you build next," these five are your honest, prepared answer.

---

## 8. Suggested live demo flow

1. **Register/login as a student** → show the whitelist gate rejecting an invalid roll number, then succeeding with a valid one.
2. **Student Dashboard** → stat cards, top matches, feed preview.
3. **Browse Alumni** → point out real match-percentage badges (SBERT cosine similarity, not random).
4. **Send Request** → type a generic message (watch the screener score sit low), then a personalized one (watch it cross 0.6 and unlock submission).
5. **Log in as the alumnus** → accept the request → show the 48-hour countdown timer appear for the student.
6. **Book a slot** within the window → show the alumnus's My Students page and the chat thread opening.
7. **Complete the session** (alumni side) → **leave feedback** (student side).
8. **Alumni Dashboard** → mentor tier badge + AI Mentor Score.
9. **Admin: Analytics/Reports** → 6 KPI cards, funnel chart, trend lines — all real, live-computed numbers.
10. **Admin: Moderation Queue** → show a borderline post caught by the toxicity layer, if one exists in seed data, or explain the pipeline.

---

## 9. If someone asks "did you do this all yourselves / is this AI-generated?"

Be direct: this was built iteratively over 9 development days, with real engineering problems solved along the way — dependency conflicts (SBERT vs. detoxify vs. Rust toolchain versions), a genuine race-condition bug in concurrent slot booking (fixed with a Postgres row lock, proven under a real concurrency test), a Celery queue misconfiguration that silently dropped background tasks, and a Windows Docker bind-mount file-watching issue that raced Alembic migrations against the app's own auto-reload. These aren't the kind of bugs you get from copy-pasting — they're the kind you get from running a real multi-service stack and debugging it under real conditions. If pressed for specifics, the day-by-day build log with every bug and fix is in `PROGRESS.md` in this repo.

---

## 17. Honest UI/UX gaps vs. a real production site

Worth knowing proactively — none of these are hard to explain away ("dev-mode pilot, not a production launch"), but pretending they don't exist if asked directly would read worse than just naming them:

**Fixed since first written:**
- ~~No collapse/hamburger sidebar~~ — **done**: `TopNav` now has a hamburger toggle (top-left), sidebar animates open/closed with a smooth width transition (`Layout.jsx`), main content reflows to fill the freed space automatically (plain flexbox, no dead space left behind).
- ~~No consistent header before login~~ — **done**: Login/Register now share a small `AuthHeader` (logo linking back to the landing page) instead of having zero branding/navigation at all; Pending now uses the full app `Layout` (sidebar + top nav) since the user is already authenticated at that point — it no longer looks like a dead-end orphan page.

**Still real gaps:**
- **Favicon is still Vite's default logo** (`/vite.svg`) — never rebranded. A 30-second fix, just never done.
- **No dynamic page titles** — every route shows the same `<title>AlumniLink AI</title>`; a real site shows "Browse Alumni | AlumniLink AI" per page.
- **No custom 404 page** — an unknown URL silently redirects to the landing page instead of showing "page not found."
- **No global error boundary** — a React rendering crash anywhere blanks the whole page instead of showing a graceful "something went wrong" screen. (We found and fixed the *specific* known trigger for this — Pydantic validation-error arrays rendered directly as JSX — but a general catch-all boundary still doesn't exist as a safety net for anything else that might slip through.)
- **No loading skeletons** — every page shows plain "Loading..." text (confirmed: 20 separate occurrences across the codebase) instead of skeleton placeholders — functionally fine, reads as unpolished next to a production site.
- **No toast/notification system** — every error is an inline red banner scoped to that page; no app-wide success/error notifications.
- **No forgot-password flow** — a real production auth system needs one; this app has none.
- **No dark mode, no accessibility audit** (contrast, keyboard nav, screen-reader labels) done beyond the ad-hoc `aria-label`s added on the password show/hide and sidebar-toggle buttons.
- **No footer** on any authenticated page (privacy policy, terms, contact) — only the pre-login landing page has one.
- **Sidebar is still fixed-width on mobile** — the collapse toggle helps, but there's no responsive breakpoint that auto-collapses it on a narrow screen; a phone user would need to manually toggle it every time.

**The honest framing if asked**: this is a pilot/demo-stage product, deliberately scoped to prove the core mentorship-matching mechanics work end-to-end — the visual/production polish items above are exactly the kind of thing that gets done in the sprint *after* the core logic is validated, not before. That's a normal, defensible engineering sequencing choice, not an oversight to hide.
