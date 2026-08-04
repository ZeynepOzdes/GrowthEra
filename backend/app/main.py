from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_default_life_areas
from app.models import (
    ai_insight,
    daily_checkin,
    focus_session,
    garden,
    goal,
    habit,
    life_area,
    task,
    user,
)
from app.routers import (
    ai,
    auth,
    daily_checkins,
    dashboard,
    focus_sessions,
    garden,
    goals,
    habits,
    life_areas,
    tasks,
    users,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()

    try:
        seed_default_life_areas(db)
    finally:
        db.close()


@app.get("/")
def read_root():
    return {
        "message": "Welcome to GrowthEra API",
        "version": settings.APP_VERSION,
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(life_areas.router)
app.include_router(goals.router)
app.include_router(habits.router)
app.include_router(daily_checkins.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(tasks.router)
app.include_router(focus_sessions.router)
app.include_router(garden.router)