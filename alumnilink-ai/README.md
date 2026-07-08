# AlumniLink AI

University alumni mentorship platform with AI-powered matching.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.111, Python 3.11 |
| Database | PostgreSQL 15 + pgvector |
| ORM | SQLAlchemy 2 (async) |
| Queue | Celery + Redis 7 |
| Frontend | React 18 + Vite + Tailwind CSS |
| Auth | JWT (python-jose + passlib) |

## Quick start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Spin up all services
docker compose up --build

# 3. App is available at:
#    Frontend: http://localhost:5173
#    Backend API: http://localhost:8000
#    API docs: http://localhost:8000/docs
```

## Project structure

```
alumnilink-ai/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, router wiring, lifespan
│   │   ├── config.py        # Pydantic settings
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   ├── models/          # 13 SQLAlchemy ORM models (pgvector VECTOR(384))
│   │   ├── routers/         # 10 FastAPI routers
│   │   ├── services/        # Business logic + ML stubs
│   │   │   └── ml/          # embeddings, screener, moderation (stubbed)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── core/            # JWT security + role-based dependencies
│   │   └── workers/         # Celery app + async tasks
│   ├── alembic/             # DB migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx          # React Router v6 + protected routes by role
│       ├── store/authStore.js  # Zustand auth store with persistence
│       ├── api/axios.js     # Axios instance with JWT interceptor
│       ├── pages/           # student / alumni / admin page sets
│       └── components/      # layout, cards, ui components
├── docker-compose.yml
└── .env.example
```

## User roles

| Role | Notes |
|------|-------|
| `student` | Active immediately after registration |
| `alumni` | Requires admin approval before login |
| `admin` | Created directly in DB (seed script) |

## ML stubs

All ML functions in `backend/app/services/ml/` return deterministic hardcoded values. Replace with real models:

- `embeddings.py` → swap `generate_embedding` with `sentence-transformers`
- `screener.py` → swap with an LLM-based scoring pipeline
- `moderation.py` → swap with OpenAI Moderation API or similar

## Creating an admin user

```bash
docker compose exec postgres psql -U alumnilink -d alumnilink_db -c \
  "UPDATE users SET role='admin', status='active' WHERE email='admin@example.com';"
```

Or register normally then promote via SQL.
