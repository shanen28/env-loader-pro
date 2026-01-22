"""Variable origin tracking and observability."""

from typing import Dict, Optional
from enum import Enum


class Origin(Enum):
    """Configuration source origins."""
    CLOUD_AZURE = "azure"
    CLOUD_AWS = "aws"
    SYSTEM = "system"
    DOCKER = "docker"
    K8S = "kubernetes"
    FILE_ENV_SPECIFIC = "file.env"
    FILE_BASE = "file"
    SCHEMA_DEFAULT = "default"
    UNKNOWN = "unknown"


class Tracer:
    """Tracks variable origins for observability and debugging."""
    
    def __init__(self, enabled: bool = False, mask_secrets: bool = True):
        """Initialize tracer.
        
        Args:
            enabled: Whether tracing is enabled
            mask_secrets: Whether to mask secrets in trace output
        """
        self.enabled = enabled
        self.mask_secrets = mask_secrets
        self._origins: Dict[str, Origin] = {}
        self._metadata: Dict[str, Dict[str, any]] = {}
    
    def record(
        self,
        key: str,
        origin: Origin,
        metadata: Optional[Dict[str, any]] = None
    ) -> None:
        """Record the origin of a variable.
        
        Args:
            key: Variable key name
            origin: Source origin
            metadata: Optional metadata about the source
        """
        if not self.enabled:
            return
        
        self._origins[key] = origin
        if metadata:
            self._metadata[key] = metadata
    
    def get_origin(self, key: str) -> Optional[Origin]:
        """Get the origin of a variable.
        
        Args:
            key: Variable key name
        
        Returns:
            Origin enum or None if not traced
        """
        return self._origins.get(key)
    
    def get_metadata(self, key: str) -> Dict[str, any]:
        """Get metadata for a variable.
        
        Args:
            key: Variable key name
        
        Returns:
            Metadata dictionary
        """
        return self._metadata.get(key, {})
    
    def get_all_origins(self) -> Dict[str, str]:
        """Get all variable origins as a dictionary.
        
        Returns:
            Dictionary mapping keys to origin strings
        """
        return {k: v.value for k, v in self._origins.items()}
    
    def get_origin_summary(self) -> Dict[str, int]:
        """Get summary of origins by type.
        
        Returns:
            Dictionary mapping origin types to counts
        """
        summary: Dict[str, int] = {}
        for origin in self._origins.values():
            summary[origin.value] = summary.get(origin.value, 0) + 1
        return summary
    
    def format_trace(self, key: str) -> str:
        """Format a trace entry for a variable.
        
        Args:
            key: Variable key name
        
        Returns:
            Formatted trace string
        """
        origin = self.get_origin(key)
        if origin is None:
            return f"{key}: unknown"
        
        metadata = self.get_metadata(key)
        if metadata:
            meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
            return f"{key}: {origin.value} ({meta_str})"
        
        return f"{key}: {origin.value}"
    
    def print_trace(self, config: Optional[Dict[str, any]] = None) -> None:
        """Print trace information.
        
        Args:
            config: Optional config dict to show values (masked if enabled)
        """
        if not self.enabled:
            return
        
        print("=== Configuration Trace ===")
        
        if config:
            from ..utils.masking import is_secret_key, mask_value
            
            for key in sorted(self._origins.keys()):
                origin = self.get_origin(key)
                value = config.get(key)
                
                # Mask secrets if enabled
                if self.mask_secrets and is_secret_key(key):
                    value_str = mask_value(value)
                else:
                    value_str = str(value)
                
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                
                print(f"  {key:30} = {value_str:30} [{origin.value if origin else 'unknown'}]")
        else:
            for key in sorted(self._origins.keys()):
                print(f"  {self.format_trace(key)}")
        
        print()
        print("=== Origin Summary ===")
        summary = self.get_origin_summary()
        for origin, count in sorted(summary.items()):
            print(f"  {origin:20} : {count} variables")
    
    def clear(self) -> None:
        """Clear all trace data."""
        self._origins.clear()
        self._metadata.clear()
