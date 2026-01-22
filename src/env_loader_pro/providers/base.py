"""Base provider interface for configuration sources."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..exceptions import ProviderError


@dataclass
class SecretMetadata:
    """Metadata about a secret value."""
    
    ttl: Optional[int] = None  # Time-to-live in seconds
    rotatable: bool = False  # Whether secret supports rotation
    last_rotated: Optional[str] = None  # ISO timestamp of last rotation
    expires_at: Optional[str] = None  # ISO timestamp when secret expires
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ttl": self.ttl,
            "rotatable": self.rotatable,
            "last_rotated": self.last_rotated,
            "expires_at": self.expires_at,
        }


@dataclass
class ProviderCapabilities:
    """Capabilities exposed by a provider."""
    
    batch: bool = True  # Supports batch operations (get_many)
    cacheable: bool = True  # Values can be cached
    rotatable: bool = False  # Supports secret rotation
    watchable: bool = False  # Supports watching for changes
    metadata: bool = False  # Provides secret metadata (TTL, etc.)
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "batch": self.batch,
            "cacheable": self.cacheable,
            "rotatable": self.rotatable,
            "watchable": self.watchable,
            "metadata": self.metadata,
        }


class BaseProvider(ABC):
    """Base class for all configuration providers."""
    
    def __init__(self):
        """Initialize provider with default capabilities."""
        self._capabilities = ProviderCapabilities()
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities.
        
        Returns:
            ProviderCapabilities instance
        """
        return self._capabilities
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get a single configuration value by key.
        
        Args:
            key: Configuration key name
            
        Returns:
            Configuration value or None if not found
        """
        pass
    
    @abstractmethod
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple configuration values.
        
        Args:
            keys: List of configuration key names
            
        Returns:
            Dictionary mapping keys to values (missing keys omitted)
        """
        pass
    
    def get_all(self) -> Dict[str, str]:
        """Get all available configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        return {}
    
    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret (optional).
        
        Args:
            key: Configuration key name
        
        Returns:
            SecretMetadata or None if not available
        """
        return None
    
    def is_available(self) -> bool:
        """Check if this provider is available/accessible.
        
        Returns:
            True if provider is available, False otherwise
        """
        return True

