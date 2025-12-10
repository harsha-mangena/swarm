"""Circuit breaker for LLM providers"""

from datetime import datetime, timedelta
from typing import Optional


class CircuitBreaker:
    """Circuit breaker pattern for provider failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0

    def allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == "closed":
            return True

        if self.state == "open":
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "half_open"
                    self.half_open_calls = 0
                    return True
            return False

        if self.state == "half_open":
            if self.half_open_calls < self.half_open_max_calls:
                return True
            return False

        return False

    def record_success(self):
        """Record successful request"""
        if self.state == "half_open":
            # Success in half-open means recovery
            self.state = "closed"
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == "closed":
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == "half_open":
            # Failure in half-open means back to open
            self.state = "open"
            self.half_open_calls = 0
        elif self.state == "closed":
            if self.failure_count >= self.failure_threshold:
                self.state = "open"

