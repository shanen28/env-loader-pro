"""Performance monitoring and guarantees."""

import time
from dataclasses import dataclass
from typing import Dict, Optional

from ..utils.logging import get_logger


@dataclass
class PerformanceSLA:
    """Performance SLA thresholds."""
    
    cold_start_ms: int = 500  # Cold start threshold
    warm_load_ms: int = 50  # Warm load threshold
    cached_ms: int = 5  # Cached load threshold


@dataclass
class PerformanceMetrics:
    """Performance metrics for configuration loading."""
    
    total_time_ms: float = 0.0
    provider_time_ms: Dict[str, float] = None
    cache_hits: int = 0
    cache_misses: int = 0
    provider_calls: int = 0
    
    def __post_init__(self):
        """Initialize default values."""
        if self.provider_time_ms is None:
            self.provider_time_ms = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_time_ms": self.total_time_ms,
            "provider_time_ms": self.provider_time_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "provider_calls": self.provider_calls,
        }


class PerformanceMonitor:
    """Monitors performance against SLA."""
    
    def __init__(self, sla: Optional[PerformanceSLA] = None, enabled: bool = True):
        """Initialize performance monitor.
        
        Args:
            sla: Performance SLA thresholds
            enabled: Whether monitoring is enabled
        """
        self.sla = sla or PerformanceSLA()
        self.enabled = enabled
        self.metrics = PerformanceMetrics()
        self.start_time: Optional[float] = None
    
    def start(self) -> None:
        """Start timing."""
        if self.enabled:
            self.start_time = time.time()
    
    def stop(self) -> None:
        """Stop timing and calculate metrics."""
        if self.enabled and self.start_time:
            elapsed_ms = (time.time() - self.start_time) * 1000
            self.metrics.total_time_ms = elapsed_ms
    
    def record_provider_call(self, provider_name: str, duration_ms: float) -> None:
        """Record a provider call.
        
        Args:
            provider_name: Provider name
            duration_ms: Call duration in milliseconds
        """
        if self.enabled:
            self.metrics.provider_calls += 1
            if provider_name not in self.metrics.provider_time_ms:
                self.metrics.provider_time_ms[provider_name] = 0.0
            self.metrics.provider_time_ms[provider_name] += duration_ms
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        if self.enabled:
            self.metrics.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        if self.enabled:
            self.metrics.cache_misses += 1
    
    def check_sla(self) -> Optional[str]:
        """Check if metrics violate SLA.
        
        Returns:
            Warning message if SLA violated, None otherwise
        """
        if not self.enabled or not self.metrics.total_time_ms:
            return None
        
        # Determine load type
        if self.metrics.cache_hits > 0 and self.metrics.cache_misses == 0:
            threshold = self.sla.cached_ms
            load_type = "cached"
        elif self.metrics.cache_misses > 0:
            threshold = self.sla.cold_start_ms
            load_type = "cold start"
        else:
            threshold = self.sla.warm_load_ms
            load_type = "warm load"
        
        if self.metrics.total_time_ms > threshold:
            return (
                f"Performance SLA violation: {load_type} load took "
                f"{self.metrics.total_time_ms:.2f}ms (threshold: {threshold}ms)"
            )
        
        return None
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current metrics.
        
        Returns:
            PerformanceMetrics instance
        """
        return self.metrics


class CircuitBreaker:
    """Simple circuit breaker for provider calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening
            timeout_seconds: Timeout before attempting to close
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def is_open(self) -> bool:
        """Check if circuit is open.
        
        Returns:
            True if circuit is open
        """
        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.timeout_seconds:
                    self.state = "half_open"
                    return False
            return True
        
        return False
    
    def should_attempt(self) -> bool:
        """Check if should attempt call.
        
        Returns:
            True if should attempt
        """
        return not self.is_open()
