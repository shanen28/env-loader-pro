"""TTL-based caching for configuration values."""

import time
from typing import Any, Dict, Optional


class Cache:
    """TTL-based cache for configuration values."""
    
    def __init__(self, ttl: int = 3600, enabled: bool = True):
        """Initialize cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
            enabled: Whether caching is enabled
        """
        self.ttl = ttl
        self.enabled = enabled
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if valid.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        if key not in self._cache:
            return None
        
        if not self._is_valid(key):
            # Remove expired entry
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def _is_valid(self, key: str) -> bool:
        """Check if a cached value is still valid.
        
        Args:
            key: Cache key
        
        Returns:
            True if value is still valid
        """
        if key not in self._timestamps:
            return False
        
        elapsed = time.time() - self._timestamps[key]
        return elapsed < self.ttl
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry(ies).
        
        Args:
            key: Specific key to invalidate, or None to clear all
        """
        if key is None:
            self._cache.clear()
            self._timestamps.clear()
        else:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.invalidate()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        valid_count = sum(1 for k in self._cache.keys() if self._is_valid(k))
        expired_count = len(self._cache) - valid_count
        
        return {
            "enabled": self.enabled,
            "ttl": self.ttl,
            "total_entries": len(self._cache),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
        }
