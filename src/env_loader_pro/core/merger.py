"""Configuration source priority resolution and merging."""

from typing import Any, Dict, List, Optional

from ..core.tracing import Origin, Tracer
from ..exceptions import ConfigurationError
from ..settings import SOURCE_PRIORITY


class ConfigurationMerger:
    """Merges configuration from multiple sources with deterministic priority."""
    
    def __init__(self, tracer: Optional[Tracer] = None):
        """Initialize merger.
        
        Args:
            tracer: Optional tracer for origin tracking
        """
        self.tracer = tracer
    
    def merge(
        self,
        sources: Dict[str, Dict[str, Any]],
        priority_order: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Merge configuration from multiple sources.
        
        Sources are merged in priority order (lower priority number = higher priority).
        Later sources override earlier ones.
        
        Args:
            sources: Dictionary mapping source names to config dicts
            priority_order: Optional custom priority order (uses default if None)
        
        Returns:
            Merged configuration dictionary
        
        Raises:
            ConfigurationError: If priority order is invalid
        """
        if priority_order is None:
            # Default priority order (1 = highest, 6 = lowest)
            priority_order = [
                "cloud_providers",
                "system",
                "docker_k8s",
                "env_specific",
                "base_file",
                "schema_defaults",
            ]
        
        # Validate all sources are in priority order
        unknown_sources = set(sources.keys()) - set(priority_order)
        if unknown_sources:
            raise ConfigurationError(
                f"Unknown sources in priority order: {unknown_sources}"
            )
        
        # Sort sources by priority (lower number = higher priority)
        sorted_sources = sorted(
            priority_order,
            key=lambda s: SOURCE_PRIORITY.get(s, 999)
        )
        
        # Merge in priority order (later = higher priority)
        merged: Dict[str, Any] = {}
        
        for source_name in sorted_sources:
            if source_name not in sources:
                continue
            
            source_config = sources[source_name]
            
            # Record origins if tracing enabled
            if self.tracer and self.tracer.enabled:
                origin = self._get_origin_for_source(source_name)
                for key in source_config.keys():
                    self.tracer.record(key, origin)
            
            # Merge (later sources override earlier ones)
            merged.update(source_config)
        
        return merged
    
    def _get_origin_for_source(self, source_name: str) -> Origin:
        """Get Origin enum for a source name.
        
        Args:
            source_name: Source name
        
        Returns:
            Origin enum
        """
        mapping = {
            "cloud_providers": Origin.CLOUD_AZURE,  # Default, can be overridden
            "system": Origin.SYSTEM,
            "docker_k8s": Origin.DOCKER,
            "env_specific": Origin.FILE_ENV_SPECIFIC,
            "base_file": Origin.FILE_BASE,
            "schema_defaults": Origin.SCHEMA_DEFAULT,
        }
        return mapping.get(source_name, Origin.UNKNOWN)
    
    def merge_with_override(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        origin: Optional[Origin] = None
    ) -> Dict[str, Any]:
        """Merge override into base (override wins).
        
        Args:
            base: Base configuration
            override: Override configuration
            origin: Optional origin for tracing
        
        Returns:
            Merged configuration
        """
        merged = dict(base)
        merged.update(override)
        
        # Record origins if tracing enabled
        if self.tracer and self.tracer.enabled and origin:
            for key in override.keys():
                self.tracer.record(key, origin)
        
        return merged
