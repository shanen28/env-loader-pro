"""Configuration diff and drift detection."""

from typing import Dict, List, Set

from ..utils.masking import is_secret_key


class ConfigDiff:
    """Tracks differences between configurations."""
    
    def __init__(
        self,
        added: Set[str],
        removed: Set[str],
        changed: Set[str],
        current: Dict[str, any],
        baseline: Dict[str, any],
    ):
        """Initialize diff.
        
        Args:
            added: Keys added in current
            removed: Keys removed from baseline
            changed: Keys that changed values
            current: Current configuration
            baseline: Baseline configuration
        """
        self.added = added
        self.removed = removed
        self.changed = changed
        self.current = current
        self.baseline = baseline
    
    def has_changes(self) -> bool:
        """Check if there are any changes.
        
        Returns:
            True if changes detected
        """
        return bool(self.added or self.removed or self.changed)
    
    def get_secret_changes(self) -> Dict[str, Set[str]]:
        """Get changes affecting secrets.
        
        Returns:
            Dictionary with 'added' and 'removed' secret keys
        """
        return {
            "added": {k for k in self.added if is_secret_key(k)},
            "removed": {k for k in self.removed if is_secret_key(k)},
        }
    
    def to_dict(self) -> Dict:
        """Convert diff to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "added": sorted(self.added),
            "removed": sorted(self.removed),
            "changed": sorted(self.changed),
            "has_changes": self.has_changes(),
        }
    
    def validate_no_secret_changes(self) -> None:
        """Validate that no secrets were added or removed.
        
        Raises:
            ValueError: If secrets were added or removed
        """
        secret_changes = self.get_secret_changes()
        if secret_changes["added"] or secret_changes["removed"]:
            msg_parts = []
            if secret_changes["added"]:
                msg_parts.append(f"Added secrets: {', '.join(sorted(secret_changes['added']))}")
            if secret_changes["removed"]:
                msg_parts.append(f"Removed secrets: {', '.join(sorted(secret_changes['removed']))}")
            raise ValueError("Secret changes detected: " + "; ".join(msg_parts))


def diff_configs(
    current: Dict[str, any],
    baseline: Dict[str, any],
) -> ConfigDiff:
    """Compare two configurations.
    
    Args:
        current: Current configuration
        baseline: Baseline configuration
    
    Returns:
        ConfigDiff instance
    """
    current_keys = set(current.keys())
    baseline_keys = set(baseline.keys())
    
    added = current_keys - baseline_keys
    removed = baseline_keys - current_keys
    changed = {
        k for k in current_keys & baseline_keys
        if current[k] != baseline[k]
    }
    
    return ConfigDiff(
        added=added,
        removed=removed,
        changed=changed,
        current=current,
        baseline=baseline,
    )
