import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AppError

WINDOW_SECONDS = 60.0


class RateLimitExceededError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"


# In-process sliding window, keyed by (bucket, client ip). Fine for a single
# container deployment; would need a shared store (e.g. Redis) behind a
# load balancer with multiple replicas.
_buckets: dict[str, list[float]] = defaultdict(list)


def rate_limit(bucket: str, limit_setting: str) -> Callable:
    async def dependency(request: Request) -> None:
        settings = get_settings()
        limit = getattr(settings, limit_setting)
        client_ip = request.client.host if request.client else "unknown"
        key = f"{bucket}:{client_ip}"

        now = time.monotonic()
        window_start = now - WINDOW_SECONDS
        hits = _buckets[key]
        while hits and hits[0] < window_start:
            hits.pop(0)

        if len(hits) >= limit:
            raise RateLimitExceededError(
                f"Rate limit exceeded for '{bucket}' ({limit} requests/minute)"
            )
        hits.append(now)

    return dependency
