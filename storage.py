import json
import os
import redis
from lifecycle import ScamPhase

redis_url = os.getenv("REDIS_URL", "rediss://default:AUp0AAIncDEyODg1YWI2Yzk0ZGY0NThlOWUyNDBjZDQxNDMwZGM2MnAxMTkwNjA@capable-rabbit-19060.upstash.io:6379")
if redis_url:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
else:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )

def get_conversation(conversation_id: str):
    data = redis_client.get(conversation_id)
    if not data:
        return None
    obj = json.loads(data)
    obj["phase"] = ScamPhase(obj["phase"])
    return obj

def save_conversation(conversation_id: str, state: dict):
    serializable = {
        "phase": state["phase"].value,
        "messages": state["messages"]
    }
    redis_client.set(conversation_id, json.dumps(serializable))