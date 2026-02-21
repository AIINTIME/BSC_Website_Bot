import json
from redis import Redis
from app.core.config import settings

# Upstash typically uses TLS => rediss://
redis_client = Redis.from_url(
    settings.UPSTASH_REDIS_URL,
    decode_responses=True,  # store/read as str
)

def _key(session_id: str) -> str:
    return f"hitbot:session:{session_id}:history"

def get_history(session_id: str) -> list[dict]:
    if not session_id:
        return []
    key = _key(session_id)
    items = redis_client.lrange(key, 0, -1)  # oldest..newest if we RPUSH
    out = []
    for s in items:
        try:
            out.append(json.loads(s))
        except Exception:
            # ignore corrupt entries
            pass
    return out

def append_turn(session_id: str, user_msg: str, bot_msg: str) -> None:
    if not session_id:
        return
    key = _key(session_id)

    # Add two messages per turn
    redis_client.rpush(key, json.dumps({"role": "user", "content": user_msg}))
    redis_client.rpush(key, json.dumps({"role": "assistant", "content": bot_msg}))

    # Keep only last N messages
    max_msgs = settings.REDIS_MAX_MESSAGES
    redis_client.ltrim(key, -max_msgs, -1)

    # Refresh TTL
    redis_client.expire(key, settings.REDIS_TTL_SECONDS)