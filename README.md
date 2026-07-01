# AlumniLink AI

### Multi-Tenant Mentorship Orchestration & Placement Intelligence Platform

![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL-blue)
![AI](https://img.shields.io/badge/AI-Embeddings%20%7C%20NLP%20%7C%20ML-green)
![License](https://img.shields.io/badge/License-Academic%20Project-gray)

---

## What Is AlumniLink AI?

AlumniLink AI is a mentorship orchestration platform that fixes the operational failures of traditional alumni-student networks. Instead of a passive directory, it actively manages the full lifecycle of a mentorship connection — from AI-screened outreach, to a strictly time-bound 48-hour booking window, to semantic profile matching — giving students faster access to relevant mentors, protecting alumni time, and giving placement cells structured engagement data.

---

## The Problem

Alumni networks are nominally active but operationally dormant. Three root causes:

| Problem | Impact |
|---|---|
| **Ghosting & fatigue** | Students send low-effort messages or don't show up; alumni stop responding after repeated bad experiences |
| **No urgency** | Scheduling tools keep requests open indefinitely, leading to abandonment |
| **No visibility** | Placement cells have zero structured data on who is mentoring whom, or what's converting to outcomes |

Existing tools (LinkedIn, Calendly, WhatsApp) solve none of these.

---

## The Solution — 3 Core Mechanisms

```
1. AI Message Screening
   Low-quality outreach is filtered before reaching alumni.
   Student gets feedback to improve, alumnus only sees quality messages.

2. 48-Hour Connection Window
   Once accepted, student has 48 hours to book a slot or it auto-releases.
   No ghosting, no indefinite pending requests.

3. Semantic Profile Matching
   Students matched to alumni by actual relevance — career goals,
   skills — not just batch year or department.

4. Bidirectional Content Feed
   Alumni post jobs/internships/resources. Students post queries.
   Both filtered by the same 4-layer moderation pipeline and
   ranked using shared embedding-based relevance.

5. Alumni Verification Gate
   New alumni registrations are held in "pending" status until
   admin-approved, following the same layered-filtering pattern
   as content moderation. Unverified alumni are excluded from
   student matching results entirely.
```

Plus: a bidirectional content feed where alumni post jobs, internships, and study resources, and students post queries (e.g. "need guidance on DBT for a data engineering internship") — both filtered through the same 4-layer moderation framework, with feed ranking working in both directions via the shared embedding infrastructure. Also includes two trained ML models predicting response likelihood and session completion.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                          │
│         Student Portal │ Alumni Portal │ Admin Portal    │
└──────────────────────────┬────────────────────────────────┘
                           │ HTTPS
                  ┌────────▼────────┐
                  │      Nginx       │
                  └────────┬────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                         │
│  Auth │ Profiles │ Matching │ Screener │ Sessions │ Feed │
│        Window Manager │ Analytics API │ Admin            │
└──────────┬─────────────────────────────────┬─────────────┘
           │                                 │
┌──────────▼──────────┐             ┌────────▼──────────┐
│    PostgreSQL         │             │      Redis          │
│    + Row-Level         │             │  48hr TTL windows   │
│    Security (RLS)       │             │  Celery broker       │
└────────────────────────┘             └────────┬────────────┘
                                                 │
                                      ┌──────────▼──────────┐
                                      │   Celery Workers      │
                                      │  Window expiry, ETL,   │
                                      │  notifications           │
                                      └────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              DS / ML Layer (Python, local)                   │
│  Sentence Embeddings │ Cosine Similarity │ NLP Classification│
│  Toxicity Detection │ Logistic Regression │ Random Forest     │
└────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (Vite) + Tailwind CSS + shadcn/ui + Recharts |
| State | Zustand |
| HTTP | Axios |
| Backend | FastAPI (Python 3.11) |
| ORM | SQLAlchemy (async) + Alembic |
| Database | PostgreSQL 15 + Row-Level Security (multi-tenant) |
| Cache / Queue | Redis 7 |
| Workers | Celery |
| Proxy | Nginx |
| Containers | Docker + Docker Compose |
| DS/ML | sentence-transformers, scikit-learn, transformers (HuggingFace), Detoxify, Pandas, NumPy |
| Deployment (Phase 2) | Azure App Service, Azure AI Language, Azure OpenAI |

**Phase 1 (build): $0 cost — everything runs locally in Docker/Codespaces.**
**Phase 2 (deploy): ~₹1600/month from Azure student credits.**

---

## Data Science & ML Concepts Used

| Concept | Where Used | Type |
|---|---|---|
| Text Embeddings | Profile matching, feed ranking | Pretrained model |
| Cosine Similarity | Ranking alumni / posts by relevance | Math/DS |
| Rule-Based Classification | Message screener, content filter (built by us) | DS |
| Zero-Shot NLP Classification | Content categorization | Pretrained model |
| Toxicity Detection | Content safety layer | Pretrained ML model |
| **Logistic Regression** | Response likelihood predictor | **Trained by us** |
| **Random Forest** | Session completion predictor | **Trained by us** |
| Feedback-Driven Tag Refinement | Profile tag weight updates (RL-inspired) | Bandit-style learning |
| Medallion ETL (Bronze/Silver/Gold) | Analytics pipeline | Data engineering |
| Row-Level Security | Multi-tenant data isolation | Data engineering |
| TTL Event Architecture | 48-hour connection window | Data engineering |

---

## User Roles & Permissions

| Role | Can Do |
|---|---|
| **Student** | Create profile, browse ranked alumni, send requests, track windows, book sessions, view personalized feed |
| **Alumnus** | Create profile, accept/decline requests, set availability, publish posts (moderated), view impact stats — *only after admin verification approval* |
| **Admin** | Manage users/sessions within department, view analytics, review moderation queue, configure thresholds, view audit logs — restricted to own tenant via RLS |

---

## Core User Journey

```
Alumnus registers → status: pending → admin verifies → status: verified
        ↓ (only verified alumni appear below)
Student browses alumni (ranked by match score)
        ↓
Sends request + message → AI screener checks quality
        ↓
Alumnus accepts → 48-hour window opens (Redis TTL)
        ↓
Student books slot within window → Session confirmed
        ↓
   (or window expires → slot auto-released, student notified)
        ↓
Session happens → Feedback collected
        ↓
Nightly ETL: Bronze → Silver → Gold → Admin Analytics Dashboard
```

---

## Project Structure

```
alumnilink-ai/
├── .devcontainer/
│   └── devcontainer.json
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth/
│   │   │   ├── profiles/
│   │   │   ├── matching/
│   │   │   ├── requests/
│   │   │   ├── windows/
│   │   │   ├── sessions/
│   │   │   ├── feed/
│   │   │   ├── moderation/
│   │   │   ├── predict/
│   │   │   └── admin/
│   │   ├── core/            # config, security, database
│   │   ├── models/          # SQLAlchemy models (Person B)
│   │   ├── services/
│   │   │   ├── ml/          # embeddings, cosine sim (Person A)
│   │   │   ├── matching/    # Person A
│   │   │   ├── moderation/  # Person A
│   │   │   ├── auth/        # Person B
│   │   │   ├── sessions/    # Person B
│   │   │   └── windows/     # Person B
│   │   ├── tasks/           # Celery tasks
│   │   └── main.py
│   ├── alembic/
│   ├── scripts/seed.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/student/   # Person B
│   │   ├── pages/alumni/    # Person B
│   │   ├── pages/admin/     # Person B
│   │   ├── components/
│   │   ├── store/
│   │   └── services/
│   ├── package.json
│   └── Dockerfile
├── nginx/nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Team & Work Split

| Track | Owner | Responsibilities |
|---|---|---|
| **Intelligence Track** | Fiyona Saji | Embeddings, matching engine, message screener, content moderation (4-layer), Logistic Regression + Random Forest models, tag refinement |
| **Systems Track** | Sibin D Saimon | Database + RLS, auth, Redis/Celery TTL windows, sessions, ETL pipeline, React frontend (all portals), deployment |

**Integration contract:** Person A exposes stateless functions (`get_match_score()`, `screen_message()`, `moderate_post()`, `predict_completion()`). Person B calls these inside API routes. No shared file edits — zero merge conflicts.

---

## Getting Started

### Prerequisites
- GitHub account with Codespaces access
- Docker (if running locally instead of Codespaces)

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/alumnilink-ai.git
cd alumnilink-ai

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build

# Run migrations
docker exec alumnilink_backend alembic upgrade head

# Seed sample data
docker exec alumnilink_backend python scripts/seed.py
```

| Service | URL |
|---|---|
| App | http://localhost |
| API Docs (Swagger) | http://localhost/api/docs |
| Health Check | http://localhost/api/v1/health |

---

## Build Progress

| Phase | Module | Status |
|---|---|---|
| 0 | Docker setup, DB schema, Auth | ⬜ |
| 0 | Alumni verification gate (pending → admin approve) | ⬜ |
| 1 | Profile + Matching engine | ⬜ |
| 1 | Message screener + Requests | ⬜ |
| 1 | 48hr TTL window (Redis/Celery) | ⬜ |
| 2 | Session booking + feedback | ⬜ |
| 3 | ML models (Logistic Regression, Random Forest) | ⬜ |
| 4 | Bidirectional content feed + moderation (alumni posts + student queries) | ⬜ |
| 5 | Analytics + ETL + polish | ⬜ |

*(Update this table as modules complete — see project board for daily tracking)*

---

## Known Limitations

- Matching/prediction models validated on synthetic + questionnaire seed data (max 100 samples), not real longitudinal data
- Message screener and moderation use pretrained general-purpose models, not fine-tuned on domain-specific data
- No calendar integration in Phase 1 (Google Calendar/Outlook sync deferred to Phase 2)
- Single department pilot only; cross-institution load untested
- Tag refinement uses bandit-style feedback learning, not full reinforcement learning (deferred — insufficient interaction data for RL convergence)
- Alumni verification is currently manual (admin approval); AI-based document/OCR verification is planned for Phase 2

---

## Roadmap

```
Phase 1 (Months 1-2): Single-department pilot — this submission
Phase 2 (Months 3-4): Multi-tenant full university rollout, SSO integration
Phase 3 (Month 5+):   B2B SaaS — license to other institutions
```

---

## Research Question

> Can constraint-aware scheduling (48-hour window) combined with AI message screening measurably improve session completion rates compared to traditional open-ended scheduling?

Target: improve completion rate from industry baseline (~40%) to above 65% in pilot.

---

## License

Academic project — Department of Statistics and Data Science.

---

<p align="center">
Built by Fiyona Saji & Sibin D Saimon<br/>
Under the guidance of Dr. Rajesh R
</p>