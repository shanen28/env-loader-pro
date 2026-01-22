"""Secret masking utilities for safe logging."""

import re
from typing import Any, Dict, List, Optional, Pattern

from ..settings import DEFAULT_SECRET_PATTERNS


def is_secret_key(key: str, patterns: Optional[List[Pattern]] = None) -> bool:
    """Check if a key should be treated as a secret.
    
    Args:
        key: Environment variable key name
        patterns: Optional list of compiled regex patterns (uses defaults if None)
    
    Returns:
        True if key matches secret patterns
    """
    if patterns is None:
        patterns = [re.compile(p, re.IGNORECASE) for p in DEFAULT_SECRET_PATTERNS]
    
    return any(p.match(key) for p in patterns)


def mask_value(value: Any, show_last: int = 4) -> str:
    """Mask a secret value for safe logging.
    
    Args:
        value: Value to mask
        show_last: Number of characters to show at the end (default: 4)
    
    Returns:
        Masked string representation
    """
    if value is None:
        return "None"
    
    s = str(value)
    if len(s) <= show_last:
        return "*" * len(s)
    
    return "*" * (len(s) - show_last) + s[-show_last:]


def mask_dict(
    config: Dict[str, Any],
    patterns: Optional[List[Pattern]] = None,
    show_last: int = 4,
    custom_secrets: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Mask secrets in a configuration dictionary.
    
    Args:
        config: Configuration dictionary
        patterns: Optional list of compiled regex patterns
        show_last: Number of characters to show at the end
        custom_secrets: Additional keys to treat as secrets
    
    Returns:
        Dictionary with masked secret values
    """
    masked = {}
    secret_keys = set(custom_secrets or [])
    
    for key, value in config.items():
        if key in secret_keys or is_secret_key(key, patterns):
            masked[key] = mask_value(value, show_last)
        else:
            masked[key] = value
    
    return masked


def mark_as_secret(key: str) -> str:
    """Mark a key as secret (for custom secret lists).
    
    This is a convenience function that returns the key unchanged.
    Use it to build custom_secrets lists.
    
    Args:
        key: Key name to mark as secret
    
    Returns:
        The key name (unchanged)
    """
    return key
