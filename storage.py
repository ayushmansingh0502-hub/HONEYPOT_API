import json
import os
import redis
from lifecycle import ScamPhase

# In-memory fallback store so the API still works if Redis is unavailable.
_memory_store: dict[str, str] = {}


def _build_redis_client():
    redis_url = os.getenv("REDIS_URL", "rediss://default:AUp0AAIncDEyODg1YWI2Yzk0ZGY0NThlOWUyNDBjZDQxNDMwZGM2MnAxMTkwNjA@capable-rabbit-19060.upstash.io:6379")
    if redis_url:
        return redis.Redis.from_url(redis_url, decode_responses=True)

    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


redis_client = _build_redis_client()


def _redis_available() -> bool:
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def get_conversation(conversation_id: str):
    data = None

    if _redis_available():
        data = redis_client.get(conversation_id)
    else:
        data = _memory_store.get(conversation_id)

    if not data:
        return None

    obj = json.loads(data)
    obj["phase"] = ScamPhase(obj["phase"])
    return obj


def save_conversation(conversation_id: str, state: dict):
    serializable = {
        "phase": state["phase"].value,
        "messages": state["messages"],
    }
    payload = json.dumps(serializable)

    if _redis_available():
        redis_client.set(conversation_id, payload)
    else:
        _memory_store[conversation_id] = payload
