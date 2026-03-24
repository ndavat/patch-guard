"""Tests for RateLimiter — written BEFORE implementation (TDD RED)."""
import pytest
import time
from unittest.mock import Mock, patch


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within rate limit are allowed."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=5, time_window=1.0)

        # Should allow 5 requests
        for i in range(5):
            assert limiter.acquire("test_api") is True

    def test_rate_limiter_blocks_requests_exceeding_limit(self):
        """Test that requests exceeding rate limit are blocked."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, time_window=1.0)

        # First 2 should succeed
        assert limiter.acquire("test_api") is True
        assert limiter.acquire("test_api") is True

        # Third should fail
        assert limiter.acquire("test_api") is False

    def test_rate_limiter_resets_after_time_window(self):
        """Test that rate limiter resets after time window expires."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, time_window=0.1)

        # Use up the limit
        assert limiter.acquire("test_api") is True
        assert limiter.acquire("test_api") is True
        assert limiter.acquire("test_api") is False

        # Wait for window to reset
        time.sleep(0.15)

        # Should allow requests again
        assert limiter.acquire("test_api") is True

    def test_rate_limiter_per_service_isolation(self):
        """Test that different services have independent rate limits."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, time_window=1.0)

        # Use up limit for service A
        assert limiter.acquire("service_a") is True
        assert limiter.acquire("service_a") is True
        assert limiter.acquire("service_a") is False

        # Service B should still have its own limit
        assert limiter.acquire("service_b") is True
        assert limiter.acquire("service_b") is True

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff with jitter calculation."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=10, time_window=1.0)

        # Test backoff calculation
        backoff_1 = limiter.calculate_backoff(attempt=1, base=1.0, max_backoff=60.0)
        backoff_2 = limiter.calculate_backoff(attempt=2, base=1.0, max_backoff=60.0)
        backoff_3 = limiter.calculate_backoff(attempt=3, base=1.0, max_backoff=60.0)

        # Should increase exponentially (with jitter, so approximate)
        assert 0 < backoff_1 <= 2.0  # 2^1 = 2
        assert 0 < backoff_2 <= 4.0  # 2^2 = 4
        assert 0 < backoff_3 <= 8.0  # 2^3 = 8

    def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit breaker opens after consecutive failures."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=10, time_window=1.0, circuit_breaker_threshold=3)

        # Record 3 consecutive failures
        limiter.record_failure("test_api")
        limiter.record_failure("test_api")
        limiter.record_failure("test_api")

        # Circuit should be open
        assert limiter.is_circuit_open("test_api") is True

    def test_circuit_breaker_closes_after_timeout(self):
        """Test that circuit breaker closes after timeout period."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(
            max_requests=10,
            time_window=1.0,
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=0.1
        )

        # Open the circuit
        limiter.record_failure("test_api")
        limiter.record_failure("test_api")
        assert limiter.is_circuit_open("test_api") is True

        # Wait for timeout
        time.sleep(0.15)

        # Circuit should be closed
        assert limiter.is_circuit_open("test_api") is False

    def test_circuit_breaker_resets_on_success(self):
        """Test that circuit breaker resets failure count on success."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=10, time_window=1.0, circuit_breaker_threshold=3)

        # Record some failures
        limiter.record_failure("test_api")
        limiter.record_failure("test_api")

        # Record success
        limiter.record_success("test_api")

        # Should not be open yet (failures reset)
        assert limiter.is_circuit_open("test_api") is False

    def test_respect_api_rate_limit_headers(self):
        """Test respecting API-specific rate limit headers."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=100, time_window=60.0)

        # Simulate API response headers
        headers = {
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset": str(int(time.time()) + 60)
        }

        limiter.update_from_headers("github_api", headers)

        # Should respect the API's limit
        remaining = limiter.get_remaining("github_api")
        assert remaining <= 5

    def test_wait_if_needed_blocks_when_limit_exceeded(self):
        """Test that wait_if_needed blocks when rate limit is exceeded."""
        from patchguard.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=1, time_window=0.2)

        # Use up the limit
        limiter.acquire("test_api")

        # This should block briefly
        start = time.time()
        limiter.wait_if_needed("test_api")
        elapsed = time.time() - start

        # Should have waited at least a bit
        assert elapsed >= 0.1
