"""Policy-as-code integration for configuration enforcement."""

import json
import os
from typing import Any, Dict, List, Optional

import yaml

from ..exceptions import ConfigurationError, ValidationError


class Policy:
    """Configuration policy for enforcement."""
    
    def __init__(
        self,
        require: Optional[List[str]] = None,
        forbid: Optional[List[str]] = None,
        ttl: Optional[Dict[str, int]] = None,
        sources: Optional[Dict[str, str]] = None,
    ):
        """Initialize policy.
        
        Args:
            require: List of required variable names
            forbid: List of forbidden variable names
            ttl: Dictionary mapping keys to TTL requirements (seconds)
            sources: Dictionary mapping keys to required sources
        """
        self.require = require or []
        self.forbid = forbid or []
        self.ttl = ttl or {}
        self.sources = sources or {}
    
    def validate(self, config: Dict[str, Any], audit: Optional[Any] = None) -> None:
        """Validate configuration against policy.
        
        Args:
            config: Configuration dictionary
            audit: Optional audit object for source checking
        
        Raises:
            ValidationError: If policy is violated
        """
        errors = []
        
        # Check required variables
        missing = set(self.require) - set(config.keys())
        if missing:
            errors.append(f"Missing required variables: {', '.join(sorted(missing))}")
        
        # Check forbidden variables
        present = set(self.forbid) & set(config.keys())
        if present:
            errors.append(f"Forbidden variables present: {', '.join(sorted(present))}")
        
        # Check TTL requirements (if audit available)
        if audit:
            for key, required_ttl in self.ttl.items():
                if key in config:
                    entry = audit.get(key)
                    # TTL validation would require metadata from providers
                    # This is a placeholder for future enhancement
        
        # Check source requirements (if audit available)
        if audit:
            for key, required_source in self.sources.items():
                if key in config:
                    entry = audit.get(key)
                    if entry and entry.source != required_source:
                        errors.append(
                            f"Variable '{key}' must come from '{required_source}', "
                            f"but came from '{entry.source}'"
                        )
        
        if errors:
            raise ValidationError("Policy violations: " + "; ".join(errors))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Create policy from dictionary.
        
        Args:
            data: Policy dictionary
        
        Returns:
            Policy instance
        """
        return cls(
            require=data.get("require", []),
            forbid=data.get("forbid", []),
            ttl=data.get("ttl", {}),
            sources=data.get("sources", {}),
        )
    
    @classmethod
    def from_file(cls, path: str) -> "Policy":
        """Load policy from file.
        
        Args:
            path: Path to policy file (JSON or YAML)
        
        Returns:
            Policy instance
        
        Raises:
            ConfigurationError: If file cannot be loaded
        """
        if not os.path.exists(path):
            raise ConfigurationError(f"Policy file not found: {path}")
        
        with open(path, "r") as f:
            if path.endswith(".yaml") or path.endswith(".yml"):
                try:
                    data = yaml.safe_load(f)
                except ImportError:
                    raise ConfigurationError(
                        "PyYAML required for YAML policies. Install: pip install pyyaml"
                    )
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "require": self.require,
            "forbid": self.forbid,
            "ttl": self.ttl,
            "sources": self.sources,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert policy to JSON string.
        
        Args:
            indent: JSON indentation
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)


def load_policy(policy_path: Optional[str] = None) -> Optional[Policy]:
    """Load policy from file or return None.
    
    Args:
        policy_path: Optional path to policy file
    
    Returns:
        Policy instance or None
    """
    if not policy_path:
        return None
    
    return Policy.from_file(policy_path)
