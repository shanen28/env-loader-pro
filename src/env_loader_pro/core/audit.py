"""Audit metadata tracking for configuration provenance."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, Optional

from ..core.tracing import Origin


@dataclass
class AuditEntry:
    """Single audit entry for a configuration variable."""
    
    key: str
    source: str  # Origin value (azure, aws, system, file, etc.)
    provider: Optional[str] = None  # Provider name if from provider
    masked: bool = True  # Whether value is masked in logs
    timestamp: datetime = None  # When variable was loaded
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (safe for JSON serialization)."""
        return {
            "key": self.key,
            "source": self.source,
            "provider": self.provider,
            "masked": self.masked,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ConfigAudit:
    """Audit trail for configuration loading."""
    
    def __init__(self):
        """Initialize empty audit."""
        self.entries: Dict[str, AuditEntry] = {}
    
    def add(
        self,
        key: str,
        source: str,
        provider: Optional[str] = None,
        masked: bool = True,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add an audit entry.
        
        Args:
            key: Variable key name
            source: Source origin (azure, aws, system, file, etc.)
            provider: Optional provider name
            masked: Whether value is masked
            timestamp: Optional timestamp (defaults to now)
        """
        entry = AuditEntry(
            key=key,
            source=source,
            provider=provider,
            masked=masked,
            timestamp=timestamp or datetime.utcnow(),
        )
        self.entries[key] = entry
    
    def get(self, key: str) -> Optional[AuditEntry]:
        """Get audit entry for a key.
        
        Args:
            key: Variable key name
        
        Returns:
            AuditEntry or None if not found
        """
        return self.entries.get(key)
    
    def to_dict(self) -> Dict:
        """Convert audit to dictionary.
        
        Returns:
            Dictionary mapping keys to audit entries
        """
        return {k: v.to_dict() for k, v in self.entries.items()}
    
    def to_json(self, indent: int = 2) -> str:
        """Convert audit to JSON string.
        
        Args:
            indent: JSON indentation
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def get_by_source(self, source: str) -> Dict[str, AuditEntry]:
        """Get all entries from a specific source.
        
        Args:
            source: Source name
        
        Returns:
            Dictionary of entries from that source
        """
        return {k: v for k, v in self.entries.items() if v.source == source}
    
    def get_summary(self) -> Dict:
        """Get summary statistics.
        
        Returns:
            Dictionary with summary stats
        """
        sources = {}
        providers = {}
        masked_count = 0
        
        for entry in self.entries.values():
            sources[entry.source] = sources.get(entry.source, 0) + 1
            if entry.provider:
                providers[entry.provider] = providers.get(entry.provider, 0) + 1
            if entry.masked:
                masked_count += 1
        
        return {
            "total_variables": len(self.entries),
            "masked_variables": masked_count,
            "sources": sources,
            "providers": providers,
        }
    
    def merge(self, other: "ConfigAudit") -> "ConfigAudit":
        """Merge another audit into this one.
        
        Args:
            other: Another ConfigAudit instance
        
        Returns:
            New ConfigAudit with merged entries
        """
        merged = ConfigAudit()
        merged.entries = {**self.entries, **other.entries}
        return merged
