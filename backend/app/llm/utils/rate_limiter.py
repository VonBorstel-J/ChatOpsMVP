import time
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for API calls with token bucket algorithm."""
    
    def __init__(self, requests_per_minute: int, burst_limit: Optional[int] = None):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute (int): Number of requests allowed per minute
            burst_limit (Optional[int]): Maximum burst size (defaults to requests_per_minute)
        """
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst_limit = burst_limit or requests_per_minute
        self.tokens = self.burst_limit
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """
        Attempt to acquire a token for an API call.
        
        Returns:
            bool: True if token acquired, False if rate limit exceeded
        """
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.burst_limit,
                self.tokens + time_passed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
            
    async def wait_for_token(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for a token to become available.
        
        Args:
            timeout (Optional[float]): Maximum time to wait in seconds
            
        Returns:
            bool: True if token acquired, False if timeout reached
        """
        start_time = time.time()
        while True:
            if await self.acquire():
                return True
                
            if timeout is not None and time.time() - start_time > timeout:
                return False
                
            await asyncio.sleep(1 / self.rate)  # Wait for approximately one token period

class UserRateLimiter:
    """Per-user rate limiting manager."""
    
    def __init__(self, requests_per_minute: int, burst_limit: Optional[int] = None):
        """
        Initialize the user rate limiter manager.
        
        Args:
            requests_per_minute (int): Number of requests allowed per minute per user
            burst_limit (Optional[int]): Maximum burst size per user
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.limiters: Dict[str, RateLimiter] = {}
        
    def get_limiter(self, user_id: str) -> RateLimiter:
        """
        Get or create a rate limiter for a specific user.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            RateLimiter: Rate limiter instance for the user
        """
        if user_id not in self.limiters:
            self.limiters[user_id] = RateLimiter(
                self.requests_per_minute,
                self.burst_limit
            )
        return self.limiters[user_id] 