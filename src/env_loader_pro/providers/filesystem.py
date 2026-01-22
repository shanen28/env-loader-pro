"""Filesystem provider for K8s mounted secrets and configmaps."""

import os
from pathlib import Path
from typing import Dict, Optional

from ..exceptions import ProviderError
from .base import BaseProvider


class FilesystemProvider(BaseProvider):
    """Provider for filesystem-mounted secrets and configmaps (K8s style).
    
    Reads from mounted directories where each file represents a key-value pair.
    """
    
    def __init__(
        self,
        secrets_path: str = "/etc/secrets",
        config_map_path: str = "/etc/config",
    ):
        """Initialize filesystem provider.
        
        Args:
            secrets_path: Path where secrets are mounted
            config_map_path: Path where config maps are mounted
        """
        self.secrets_path = Path(secrets_path)
        self.config_map_path = Path(config_map_path)
    
    def get(self, key: str) -> Optional[str]:
        """Get value from filesystem mount.
        
        Checks secrets first, then config maps.
        
        Args:
            key: Configuration key name
        
        Returns:
            Configuration value or None if not found
        """
        # Try secrets first
        secret_file = self.secrets_path / key
        if secret_file.exists() and secret_file.is_file():
            try:
                return secret_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                raise ProviderError(f"Failed to read secret file '{key}': {e}")
        
        # Try config map
        config_file = self.config_map_path / key
        if config_file.exists() and config_file.is_file():
            try:
                return config_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                raise ProviderError(f"Failed to read config file '{key}': {e}")
        
        return None
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values.
        
        Args:
            keys: List of configuration key names
        
        Returns:
            Dictionary mapping keys to values (missing keys omitted)
        """
        result = {}
        for key in keys:
            try:
                value = self.get(key)
                if value is not None:
                    result[key] = value
            except ProviderError:
                pass
        return result
    
    def get_all(self) -> Dict[str, str]:
        """Get all available values from mounted paths.
        
        Returns:
            Dictionary of all configuration values
        """
        result = {}
        
        # Read from secrets
        if self.secrets_path.exists():
            for item in self.secrets_path.iterdir():
                if item.is_file():
                    try:
                        value = item.read_text(encoding="utf-8").strip()
                        result[item.name] = value
                    except Exception:
                        pass
        
        # Read from config maps (don't override secrets)
        if self.config_map_path.exists():
            for item in self.config_map_path.iterdir():
                if item.is_file() and item.name not in result:
                    try:
                        value = item.read_text(encoding="utf-8").strip()
                        result[item.name] = value
                    except Exception:
                        pass
        
        return result
    
    def is_available(self) -> bool:
        """Check if filesystem mounts are available.
        
        Returns:
            True if at least one mount path exists
        """
        return (
            self.secrets_path.exists() or
            self.config_map_path.exists()
        )
