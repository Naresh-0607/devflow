import math
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException, status

from app.config import settings


class SlidingWindowRateLimiter:
    """Small in-process rate limiter keyed by API key (device).

    This protects the ingestion endpoint from runaway hooks or a single leaked
    key. It is intentionally dependency-free; when the API runs with multiple
    workers each worker keeps its own window, which is acceptable for v1.
    """

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()
        self._checks = 0

    def check(self, key: str) -> None:
        if self.limit <= 0:
            return

        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            cutoff = now - self.window_seconds

            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.limit:
                retry_after = max(1, math.ceil(hits[0] + self.window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Rate limit exceeded: at most {self.limit} events per "
                        f"{int(self.window_seconds)} seconds per API key"
                    ),
                    headers={"Retry-After": str(retry_after)},
                )

            hits.append(now)
            self._checks += 1
            # Periodically drop keys that have gone quiet so memory stays bounded.
            if self._checks % 1000 == 0:
                self._prune(cutoff)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._checks = 0

    def _prune(self, cutoff: float) -> None:
        for key in [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            self._hits.pop(key, None)


event_rate_limiter = SlidingWindowRateLimiter(settings.event_rate_limit_per_minute)
