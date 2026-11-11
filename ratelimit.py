import time
from collections import defaultdict, deque


class RateLimiter:
    """In-memory limit per key.

    Only works with a single server worker (uvicorn --workers 1),
    because each worker keeps its own count. Counts reset on restart.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        timestamps = self.requests[key]
        while timestamps and now - timestamps[0] >= self.window_seconds:
            timestamps.popleft()
        if len(timestamps) >= self.max_requests:
            return False
        timestamps.append(now)
        return True