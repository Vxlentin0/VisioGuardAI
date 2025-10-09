from fastapi import HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import time

class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = {}

    async def check(self, key: str):
        now = time.time()
        if key not in self.timestamps:
            self.timestamps[key] = []
        
        self.timestamps[key] = [t for t in self.timestamps[key] if t > now - self.period]
        
        if len(self.timestamps[key]) >= self.calls:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )