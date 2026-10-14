from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .redis_client import wait_for_redis
from .routers import auth, system

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL tables are created and Redis is reachable
    logger.info("Initializing services: PostgreSQL & Redis...")
    try:
        init_db()
        wait_for_redis()
        logger.info("Database and Redis connections confirmed.")
    except Exception as e:
        logger.error(f"Startup initialization warning: {e}")
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Dynamic WebApp with FastAPI, PostgreSQL, and Redis for email verification workflow",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development and container communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(system.router)

@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "documentation": "/docs",
        "health": "/api/health",
        "status": "/api/system/status"
    }
