import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

logger = logging.getLogger("uvicorn.error")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db(max_retries: int = 15, delay_seconds: int = 2):
    """Wait for PostgreSQL database to be reachable before starting application."""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL database.")
                return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay_seconds}s...")
            time.sleep(delay_seconds)
    raise RuntimeError("Could not connect to PostgreSQL after multiple retries.")

def init_db():
    """Create all tables in PostgreSQL if they don't exist."""
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
