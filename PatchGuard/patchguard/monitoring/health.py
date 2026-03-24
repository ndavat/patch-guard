"""Health checker for PatchGuard agent."""
import time
import threading
from typing import Dict, Any, Optional
from unittest.mock import Mock


class HealthChecker:
    """Health checker for PatchGuard agent.

    Features:
    - Liveness check (service is running)
    - Readiness check (service is ready to serve traffic)
    - Dependency checks (database, external APIs, etc.)
    - Configurable health check intervals
    """

    def __init__(self):
        """Initialize health checker."""
        self._start_time = time.time()
        self._last_health_check = 0
        self._health_status = {
            "liveness": True,
            "readiness": True,
            "timestamp": self._start_time,
            "version": "0.1.0",
            "uptime_seconds": 0
        }
        self._dependencies: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def check_liveness(self) -> bool:
        """Check if service is alive (running).

        Returns:
            True if service is alive, False otherwise
        """
        # Simple liveness check - if we can respond, we're alive
        with self._lock:
            self._health_status["timestamp"] = time.time()
            self._health_status["uptime_seconds"] = time.time() - self._start_time
            return self._health_status["liveness"]

    def check_readiness(self) -> bool:
        """Check if service is ready to serve traffic.

        Returns:
            True if service is ready, False otherwise
        """
        with self._lock:
            # Check all dependencies
            ready = self._health_status["readiness"]
            for dep_name, dep_status in self._dependencies.items():
                ready = ready and dep_status

            self._health_status["timestamp"] = time.time()
            self._health_status["uptime_seconds"] = time.time() - self._start_time
            self._health_status["readiness"] = ready
            return ready

    def set_dependency_healthy(self, name: str, healthy: bool = True) -> None:
        """Set dependency health status.

        Args:
            name: Dependency name
            healthy: Whether dependency is healthy
        """
        with self._lock:
            self._dependencies[name] = healthy
            # Update overall readiness
            all_healthy = all(self._dependencies.values()) if self._dependencies else True
            self._health_status["readiness"] = self._health_status["liveness"] and all_healthy

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status.

        Returns:
            Dictionary with health status information
        """
        with self._lock:
            return self._health_status.copy()

    def simulate_startup_delay(self, seconds: float = 2.0) -> None:
        """Simulate startup delay for testing readiness checks.

        Args:
            seconds: Delay in seconds
        """
        time.sleep(seconds)
        with self._lock:
            self._health_status["readiness"] = True

    def _check_redis(self) -> bool:
        """Check Redis connectivity (mock implementation).

        Returns:
            True if Redis is accessible
        """
        # In real implementation, this would attempt to connect to Redis
        return True

    def _check_github_api(self) -> bool:
        """Check GitHub API connectivity (mock implementation).

        Returns:
            True if GitHub API is accessible
        """
        # In real implementation, this would make a test API call
        return True

    def _check_external_services(self) -> Dict[str, bool]:
        """Check all external service dependencies.

        Returns:
            Dictionary of service names to health status
        """
        return {
            "redis": self._check_redis(),
            "github_api": self._check_github_api(),
        }
