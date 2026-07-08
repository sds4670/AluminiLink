from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import create_all_tables

from app.routers import auth, profiles, matching, requests, windows, sessions, availability, feed, admin, screener


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="University alumni mentorship platform with AI-powered matching",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(matching.router)
app.include_router(requests.router)
app.include_router(windows.router)
app.include_router(sessions.router)
app.include_router(availability.router)
app.include_router(feed.router)
app.include_router(admin.router)
app.include_router(screener.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
