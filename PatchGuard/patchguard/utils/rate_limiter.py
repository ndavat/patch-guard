"""Centralized rate limiter with token bucket, exponential backoff, and circuit breaker."""
import time
import random
from typing import Dict, Optional
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ServiceState:
    """State tracking for a single service/API."""
    tokens: float
    last_refill: float
    failure_count: int = 0
    circuit_open_until: Optional[float] = None
    last_success: Optional[float] = None


class RateLimiter:
    """Token bucket rate limiter with circuit breaker pattern.

    Features:
    - Token bucket algorithm for rate limiting
    - Per-service isolation
    - Exponential backoff with full jitter
    - Circuit breaker (opens after N consecutive failures)
    - API header-based rate limit updates
    """

    def __init__(
        self,
        max_requests: int = 10,
        time_window: float = 1.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 300.0
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
            circuit_breaker_threshold: Consecutive failures before circuit opens
            circuit_breaker_timeout: Seconds to wait before closing circuit
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        self._services: Dict[str, ServiceState] = {}
        self._lock = Lock()

    def _get_or_create_state(self, service: str) -> ServiceState:
        """Get or create state for a service."""
        if service not in self._services:
            self._services[service] = ServiceState(
                tokens=float(self.max_requests),
                last_refill=time.time()
            )
        return self._services[service]

    def _refill_tokens(self, state: ServiceState) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - state.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = (elapsed / self.time_window) * self.max_requests
        state.tokens = min(self.max_requests, state.tokens + tokens_to_add)
        state.last_refill = now

    def acquire(self, service: str) -> bool:
        """Try to acquire a token for the service.

        Args:
            service: Service/API identifier

        Returns:
            True if token acquired, False if rate limit exceeded
        """
        with self._lock:
            state = self._get_or_create_state(service)
            self._refill_tokens(state)

            if state.tokens >= 1.0:
                state.tokens -= 1.0
                return True
            return False

    def wait_if_needed(self, service: str, timeout: float = 60.0) -> None:
        """Wait until a token is available or timeout.

        Args:
            service: Service/API identifier
            timeout: Maximum time to wait in seconds
        """
        start = time.time()

        while time.time() - start < timeout:
            if self.acquire(service):
                return

            # Calculate wait time based on token refill rate
            with self._lock:
                state = self._get_or_create_state(service)
                wait_time = min(0.1, self.time_window / self.max_requests)

            time.sleep(wait_time)

    def calculate_backoff(
        self,
        attempt: int,
        base: float = 1.0,
        max_backoff: float = 60.0
    ) -> float:
        """Calculate exponential backoff with full jitter.

        Args:
            attempt: Attempt number (1-indexed)
            base: Base delay in seconds
            max_backoff: Maximum backoff in seconds

        Returns:
            Backoff time in seconds
        """
        # Exponential backoff: base * 2^attempt
        backoff = min(max_backoff, base * (2 ** attempt))

        # Full jitter: random value between 0 and backoff
        return random.uniform(0, backoff)

    def record_failure(self, service: str) -> None:
        """Record a failure for circuit breaker tracking.

        Args:
            service: Service/API identifier
        """
        with self._lock:
            state = self._get_or_create_state(service)
            state.failure_count += 1

            # Open circuit if threshold reached
            if state.failure_count >= self.circuit_breaker_threshold:
                state.circuit_open_until = time.time() + self.circuit_breaker_timeout

    def record_success(self, service: str) -> None:
        """Record a success, resetting failure count.

        Args:
            service: Service/API identifier
        """
        with self._lock:
            state = self._get_or_create_state(service)
            state.failure_count = 0
            state.last_success = time.time()
            state.circuit_open_until = None

    def is_circuit_open(self, service: str) -> bool:
        """Check if circuit breaker is open for a service.

        Args:
            service: Service/API identifier

        Returns:
            True if circuit is open (service unavailable)
        """
        with self._lock:
            state = self._get_or_create_state(service)

            if state.circuit_open_until is None:
                return False

            # Check if timeout has passed
            if time.time() >= state.circuit_open_until:
                # Close circuit
                state.circuit_open_until = None
                state.failure_count = 0
                return False

            return True

    def update_from_headers(
        self,
        service: str,
        headers: Dict[str, str]
    ) -> None:
        """Update rate limit from API response headers.

        Args:
            service: Service/API identifier
            headers: HTTP response headers
        """
        with self._lock:
            state = self._get_or_create_state(service)

            # Check for common rate limit headers
            remaining = None
            reset_time = None

            # GitHub style
            if "X-RateLimit-Remaining" in headers:
                remaining = int(headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in headers:
                reset_time = int(headers["X-RateLimit-Reset"])

            # GitLab style
            if "RateLimit-Remaining" in headers:
                remaining = int(headers["RateLimit-Remaining"])
            if "RateLimit-Reset" in headers:
                reset_time = int(headers["RateLimit-Reset"])

            # Update state if we got valid data
            if remaining is not None:
                state.tokens = float(remaining)

            if reset_time is not None:
                state.last_refill = float(reset_time)

    def get_remaining(self, service: str) -> int:
        """Get remaining tokens for a service.

        Args:
            service: Service/API identifier

        Returns:
            Number of remaining tokens
        """
        with self._lock:
            state = self._get_or_create_state(service)
            self._refill_tokens(state)
            return int(state.tokens)
