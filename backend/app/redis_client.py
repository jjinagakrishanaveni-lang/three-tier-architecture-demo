import json
import logging
import time
from typing import Optional, Dict, Any, List
import redis

from .config import settings

logger = logging.getLogger("uvicorn.error")

# Global Redis client connection pool
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True
)

def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)

def wait_for_redis(max_retries: int = 15, delay_seconds: int = 2):
    """Wait for Redis server to be reachable before starting application."""
    client = get_redis_client()
    for attempt in range(1, max_retries + 1):
        try:
            if client.ping():
                logger.info("Successfully connected to Redis.")
                return True
        except Exception as e:
            logger.warning(f"Redis connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay_seconds}s...")
            time.sleep(delay_seconds)
    raise RuntimeError("Could not connect to Redis after multiple retries.")

def save_pending_registration(token: str, name: str, email: str, hashed_password: str) -> bool:
    """
    Requirement 3: Store the pending registration details and verification token temporarily in Redis.
    Uses TTL (e.g., 900 seconds = 15 minutes) to ensure temporary storage.
    """
    client = get_redis_client()
    
    # Check if there was an old pending token for this email and clean it
    old_token = client.get(f"pending_email:{email.lower()}")
    if old_token:
        client.delete(f"pending_user:{old_token}")
        
    data = {
        "name": name,
        "email": email.lower(),
        "hashed_password": hashed_password,
        "created_at": time.time()
    }
    
    ttl = settings.PENDING_REGISTRATION_TTL
    
    pipe = client.pipeline()
    pipe.set(f"pending_user:{token}", json.dumps(data), ex=ttl)
    pipe.set(f"pending_email:{email.lower()}", token, ex=ttl)
    pipe.execute()
    
    logger.info(f"Stored pending registration in Redis for email={email} with token={token[:8]}... (TTL: {ttl}s)")
    return True

def get_pending_registration(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve temporary registration details from Redis using verification token."""
    client = get_redis_client()
    raw_data = client.get(f"pending_user:{token}")
    if not raw_data:
        return None
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        return None

def delete_pending_registration(token: str, email: Optional[str] = None):
    """Delete pending registration after verification or upon expiration."""
    client = get_redis_client()
    keys_to_delete = [f"pending_user:{token}"]
    if email:
        keys_to_delete.append(f"pending_email:{email.lower()}")
    client.delete(*keys_to_delete)
    logger.info(f"Removed pending registration from Redis for token={token[:8]}...")

def is_email_pending_in_redis(email: str) -> bool:
    """Check if an email has a pending verification in Redis."""
    client = get_redis_client()
    return bool(client.exists(f"pending_email:{email.lower()}"))

def count_pending_registrations() -> int:
    """Get count of active pending registrations in Redis."""
    client = get_redis_client()
    keys = client.keys("pending_user:*")
    return len(keys)

def store_simulated_email(email_record: Dict[str, Any]):
    """Store recent simulated emails in Redis for dev preview/testing convenience."""
    client = get_redis_client()
    key = "dev:simulated_emails"
    client.lpush(key, json.dumps(email_record))
    client.ltrim(key, 0, 19)  # Keep latest 20 emails

def get_recent_simulated_emails() -> List[Dict[str, Any]]:
    """Fetch recent simulated emails from Redis."""
    client = get_redis_client()
    key = "dev:simulated_emails"
    raw_items = client.lrange(key, 0, 19)
    emails = []
    for item in raw_items:
        try:
            emails.append(json.loads(item))
        except Exception:
            continue
    return emails
