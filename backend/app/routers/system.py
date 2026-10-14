from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..models import User
from ..redis_client import get_redis_client, count_pending_registrations, get_recent_simulated_emails
from ..schemas import SystemStatusResponse

router = APIRouter(prefix="/api", tags=["System & Diagnostics"])

@router.get("/health", summary="Service healthcheck endpoint")
def healthcheck():
    return {"status": "healthy"}

@router.get("/system/status", response_model=SystemStatusResponse, summary="Live status of DB and Redis")
def get_system_status(db: Session = Depends(get_db)):
    """Check connectivity to PostgreSQL and Redis, plus record counts."""
    # Check Postgres
    db_status = "Disconnected"
    user_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_status = "Connected"
        user_count = db.query(User).count()
    except Exception as e:
        db_status = f"Error: {str(e)}"

    # Check Redis
    redis_status = "Disconnected"
    pending_count = 0
    try:
        r = get_redis_client()
        if r.ping():
            redis_status = "Connected"
            pending_count = count_pending_registrations()
    except Exception as e:
        redis_status = f"Error: {str(e)}"

    return SystemStatusResponse(
        status="operational" if db_status == "Connected" and redis_status == "Connected" else "degraded",
        database=db_status,
        redis=redis_status,
        users_count=user_count,
        pending_registrations_count=pending_count
    )

@router.get("/dev/recent-emails", summary="View recent simulated emails for rapid testing")
def get_simulated_emails():
    """Retrieve simulated emails stored in Redis."""
    try:
        emails = get_recent_simulated_emails()
        return {"emails": emails}
    except Exception as e:
        return {"emails": [], "error": str(e)}
