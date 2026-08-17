"""FastAPI application entry point for Koota Match Engine."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.db.seed_kootas import seed_kootas
from app.api.routes_profiles import router as profiles_router
from app.api.routes_match import router as match_router
from app.api.routes_auth import router as auth_router
from app.api.routes_weekly import router as weekly_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and ensure Kootas are seeded on startup
    await init_db()
    await seed_kootas()
    yield


app = FastAPI(
    title="Koota Match Engine API",
    description="42-Koota scientific marital compatibility matching service (India-focused)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire API routers
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(match_router)
app.include_router(weekly_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Render & keepalive cron."""
    return {"status": "healthy", "service": "koota-match-engine", "version": "1.0.0"}


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Koota Match Engine",
        "description": "42-Koota Marital Compatibility System",
        "docs_url": "/docs",
    }
