"""Docker and Kubernetes secrets provider."""

import os
from pathlib import Path
from typing import Dict, Optional

from ..exceptions import ProviderError
from .base import BaseProvider


class DockerSecretsProvider(BaseProvider):
    """Provider for Docker secrets (mounted at /run/secrets)."""
    
    def __init__(self, secrets_path: str = "/run/secrets"):
        """Initialize Docker secrets provider.
        
        Args:
            secrets_path: Path where Docker secrets are mounted
        """
        self.secrets_path = Path(secrets_path)
    
    def get(self, key: str) -> Optional[str]:
        """Get secret from Docker secrets directory."""
        secret_file = self.secrets_path / key
        if not secret_file.exists():
            return None
        
        try:
            return secret_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            raise ProviderError(f"Failed to read Docker secret '{key}': {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple secrets."""
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
        """Get all available Docker secrets."""
        if not self.secrets_path.exists():
            return {}
        
        result = {}
        try:
            for secret_file in self.secrets_path.iterdir():
                if secret_file.is_file():
                    try:
                        value = secret_file.read_text(encoding="utf-8").strip()
                        result[secret_file.name] = value
                    except Exception:
                        # Skip files we can't read
                        pass
        except Exception as e:
            raise ProviderError(f"Failed to list Docker secrets: {e}")
        
        return result
    
    def is_available(self) -> bool:
        """Check if Docker secrets directory exists."""
        return self.secrets_path.exists() and self.secrets_path.is_dir()


class KubernetesSecretsProvider(BaseProvider):
    """Provider for Kubernetes secrets and config maps."""
    
    def __init__(
        self,
        secrets_path: str = "/etc/secrets",
        config_map_path: str = "/etc/config",
    ):
        """Initialize Kubernetes secrets provider.
        
        Args:
            secrets_path: Path where Kubernetes secrets are mounted
            config_map_path: Path where Kubernetes config maps are mounted
        """
        self.secrets_path = Path(secrets_path)
        self.config_map_path = Path(config_map_path)
    
    def _read_from_path(self, key: str, base_path: Path) -> Optional[str]:
        """Read value from a mounted Kubernetes path."""
        value_file = base_path / key
        if not value_file.exists():
            return None
        
        try:
            return value_file.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Kubernetes secrets or config maps.
        
        Checks secrets first, then config maps.
        """
        # Try secrets first
        value = self._read_from_path(key, self.secrets_path)
        if value is not None:
            return value
        
        # Try config maps
        value = self._read_from_path(key, self.config_map_path)
        return value
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def get_all(self) -> Dict[str, str]:
        """Get all available Kubernetes secrets and config maps."""
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
        """Check if Kubernetes paths exist."""
        return (
            self.secrets_path.exists() or
            self.config_map_path.exists()
        )

