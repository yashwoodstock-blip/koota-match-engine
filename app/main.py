"""FastAPI application entry point for Koota Match Engine with structured observability."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, get_db
from app.db.seed_kootas import seed_kootas
from app.api.routes_profiles import router as profiles_router
from app.api.routes_match import router as match_router
from app.api.routes_auth import router as auth_router
from app.api.routes_weekly import router as weekly_router
from app.api.routes_following import router as following_router
from app.api.routes_interest import router as interest_router
from app.api.routes_on_demand import router as on_demand_router

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("koota")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and ensure Kootas are seeded on startup
    try:
        await init_db()
        await seed_kootas()
        logger.info("Database initialized and 42 Kootas verified.")
    except Exception as e:
        logger.warning(f"Startup DB init warning: {e}")
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


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Structured request logging and global 5xx error capture."""
    try:
        response: Response = await call_next(request)
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            logger.warning(f"RateLimit hit: {request.method} {request.url.path}")
        elif response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            logger.info(f"AuthGate: {request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as exc:
        logger.exception(f"Unhandled 5xx Server Error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal matching engine error. Please try again later."},
        )


# Wire API routers
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(on_demand_router)
app.include_router(following_router)
app.include_router(interest_router)
app.include_router(match_router)
app.include_router(weekly_router)


@app.get("/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Live health check verifying application and database connectivity."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    is_ready = db_status == "healthy"
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_ready else "degraded",
            "database": db_status,
            "service": "koota-match-engine",
            "version": "1.0.0",
        },
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Koota Match Engine",
        "description": "42-Koota Marital Compatibility System",
        "docs_url": "/docs",
    }
