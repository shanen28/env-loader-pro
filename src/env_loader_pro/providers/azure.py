"""Azure Key Vault provider."""

from typing import Any, Dict, Optional

from ..exceptions import ProviderError
from .base import BaseProvider


class AzureKeyVaultProvider(BaseProvider):
    """Provider for Azure Key Vault secrets."""
    
    def __init__(
        self,
        vault_url: str,
        credential: Optional[Any] = None,
        cache: bool = True,
        cache_ttl: int = 3600,
    ):
        """Initialize Azure Key Vault provider.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://myvault.vault.azure.net)
            credential: Azure credential object (uses DefaultAzureCredential if None)
            cache: Enable caching of secrets
            cache_ttl: Cache TTL in seconds
        """
        self.vault_url = vault_url
        self._cache = {} if cache else None
        self._cache_ttl = cache_ttl
        self._cache_timestamps = {}
        self._credential = credential
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Azure Key Vault client."""
        if self._client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
                
                credential = self._credential or DefaultAzureCredential()
                self._client = SecretClient(
                    vault_url=self.vault_url,
                    credential=credential
                )
            except ImportError:
                raise ProviderError(
                    "azure-identity and azure-keyvault-secrets are required. "
                    "Install with: pip install env-loader-pro[azure]"
                )
            except Exception as e:
                raise ProviderError(f"Failed to initialize Azure Key Vault client: {e}")
        
        return self._client
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached value is still valid."""
        if self._cache is None:
            return False
        if key not in self._cache:
            return False
        import time
        elapsed = time.time() - self._cache_timestamps.get(key, 0)
        return elapsed < self._cache_ttl
    
    def get(self, key: str) -> Optional[str]:
        """Get secret from Azure Key Vault."""
        # Check cache first
        if self._cache and self._is_cache_valid(key):
            return self._cache[key]
        
        try:
            client = self._get_client()
            secret = client.get_secret(key)
            value = secret.value
            
            # Update cache
            if self._cache is not None:
                import time
                self._cache[key] = value
                self._cache_timestamps[key] = time.time()
            
            return value
        except Exception as e:
            raise ProviderError(f"Failed to get secret '{key}' from Azure Key Vault: {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple secrets from Azure Key Vault."""
        result = {}
        for key in keys:
            try:
                value = self.get(key)
                if value is not None:
                    result[key] = value
            except ProviderError:
                # Skip keys that fail
                pass
        return result
    
    def is_available(self) -> bool:
        """Check if Azure Key Vault is accessible."""
        try:
            self._get_client()
            return True
        except Exception:
            return False

