"""
HTTP utilities
"""

from __future__ import annotations
from collections import deque
import time

from src import thread


class RateLimiter:
    """
    HTTP rate limiter
    """
    def __init__(self, rate_limit: int = 15) -> RateLimiter:
        self._rate_limit: int = rate_limit
        self._request_times: deque = deque()

    @thread.thread_safe
    def rate_limit(self) -> None:
        """
        Thread safe method that returns when the next rate limited HTTP call can be made
        """
        while True:
            now = time.time()

            while self._request_times:
                if now - self._request_times[0] > 1:
                    self._request_times.popleft()
                else:
                    break

            if len(self._request_times) < self._rate_limit:
                break

            time.sleep(0.00001)

        self._request_times.append(time.time())

    def __enter__(self) -> None:
        """
        Context manager entry
        """
        return self.rate_limit()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit
        """
        pass
