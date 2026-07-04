from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time
from typing import DefaultDict

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from config import config

config.validate_runtime_requirements()

API_KEY = config.api.api_key
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

_rate_limit_buckets: DefaultDict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    cutoff = now - config.api.rate_limit_window_seconds
    with _rate_limit_lock:
        bucket = _rate_limit_buckets[client_ip]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= config.api.rate_limit_requests:
            return True
        bucket.append(now)
        return False


def reset_rate_limits() -> None:
    with _rate_limit_lock:
        _rate_limit_buckets.clear()


def rate_limit_stats() -> dict:
    with _rate_limit_lock:
        active_clients = len(_rate_limit_buckets)
        current_depth = sum(len(bucket) for bucket in _rate_limit_buckets.values())
    return {
        "active_clients": active_clients,
        "tracked_requests": current_depth,
        "window_seconds": config.api.rate_limit_window_seconds,
        "requests_per_window": config.api.rate_limit_requests,
    }
