"""AWS providers (Secrets Manager and SSM Parameter Store)."""

import json
from typing import Any, Dict, List, Optional

from ..exceptions import ProviderError
from .base import BaseProvider


class AWSSecretsManagerProvider(BaseProvider):
    """Provider for AWS Secrets Manager."""
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        region_name: Optional[str] = None,
        cache: bool = True,
        cache_ttl: int = 3600,
    ):
        """Initialize AWS Secrets Manager provider.
        
        Args:
            secret_id: Secret ID or ARN (if None, uses get_many with explicit keys)
            region_name: AWS region name
            cache: Enable caching
            cache_ttl: Cache TTL in seconds
        """
        self.secret_id = secret_id
        self.region_name = region_name
        self._cache = {} if cache else None
        self._cache_ttl = cache_ttl
        self._cache_timestamps = {}
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of AWS Secrets Manager client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "secretsmanager",
                    region_name=self.region_name
                )
            except ImportError:
                raise ProviderError(
                    "boto3 is required. Install with: pip install env-loader-pro[aws]"
                )
            except Exception as e:
                raise ProviderError(f"Failed to initialize AWS Secrets Manager client: {e}")
        
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
        """Get secret from AWS Secrets Manager.
        
        If secret_id is set, treats key as JSON field name.
        Otherwise, treats key as secret ID.
        """
        # Check cache
        if self._cache and self._is_cache_valid(key):
            return self._cache[key]
        
        try:
            client = self._get_client()
            
            if self.secret_id:
                # Fetch JSON secret and extract field
                response = client.get_secret_value(SecretId=self.secret_id)
                secret = response.get("SecretString", "{}")
                
                # Try to parse as JSON
                if secret.startswith("{"):
                    data = json.loads(secret)
                    value = data.get(key)
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    elif value is not None:
                        value = str(value)
                else:
                    # Plain text secret, use as-is if key matches secret_id
                    value = secret if key == self.secret_id else None
            else:
                # Treat key as secret ID
                response = client.get_secret_value(SecretId=key)
                secret = response.get("SecretString", "")
                
                # Try to parse as JSON
                if secret.startswith("{"):
                    data = json.loads(secret)
                    # If it's a dict, return as JSON string
                    value = json.dumps(data) if isinstance(data, dict) else secret
                else:
                    value = secret
            
            # Update cache
            if value is not None and self._cache is not None:
                import time
                self._cache[key] = value
                self._cache_timestamps[key] = time.time()
            
            return value
        except Exception as e:
            raise ProviderError(f"Failed to get secret '{key}' from AWS Secrets Manager: {e}")
    
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
    
    def is_available(self) -> bool:
        """Check if AWS Secrets Manager is accessible."""
        try:
            self._get_client()
            return True
        except Exception:
            return False


class AWSSSMProvider(BaseProvider):
    """Provider for AWS Systems Manager Parameter Store."""
    
    def __init__(
        self,
        prefix: Optional[str] = None,
        region_name: Optional[str] = None,
        decrypt: bool = True,
        cache: bool = True,
        cache_ttl: int = 3600,
    ):
        """Initialize AWS SSM Parameter Store provider.
        
        Args:
            prefix: Parameter prefix (e.g., "/my-app/dev/")
            region_name: AWS region name
            decrypt: Automatically decrypt SecureString parameters
            cache: Enable caching
            cache_ttl: Cache TTL in seconds
        """
        self.prefix = prefix or ""
        self.region_name = region_name
        self.decrypt = decrypt
        self._cache = {} if cache else None
        self._cache_ttl = cache_ttl
        self._cache_timestamps = {}
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of AWS SSM client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "ssm",
                    region_name=self.region_name
                )
            except ImportError:
                raise ProviderError(
                    "boto3 is required. Install with: pip install env-loader-pro[aws]"
                )
            except Exception as e:
                raise ProviderError(f"Failed to initialize AWS SSM client: {e}")
        
        return self._client
    
    def _make_parameter_name(self, key: str) -> str:
        """Convert key to full parameter name."""
        if self.prefix:
            # Ensure prefix ends with /
            prefix = self.prefix if self.prefix.endswith("/") else f"{self.prefix}/"
            return f"{prefix}{key}"
        return key
    
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
        """Get parameter from AWS SSM."""
        # Check cache
        if self._cache and self._is_cache_valid(key):
            return self._cache[key]
        
        try:
            client = self._get_client()
            param_name = self._make_parameter_name(key)
            
            response = client.get_parameter(
                Name=param_name,
                WithDecryption=self.decrypt
            )
            
            value = response["Parameter"]["Value"]
            
            # Update cache
            if self._cache is not None:
                import time
                self._cache[key] = value
                self._cache_timestamps[key] = time.time()
            
            return value
        except client.exceptions.ParameterNotFound:
            return None
        except Exception as e:
            raise ProviderError(f"Failed to get parameter '{key}' from AWS SSM: {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple parameters."""
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
        """Get all parameters under prefix."""
        if not self.prefix:
            return {}
        
        try:
            client = self._get_client()
            prefix = self.prefix if self.prefix.endswith("/") else f"{self.prefix}/"
            
            result = {}
            paginator = client.get_paginator("get_parameters_by_path")
            
            for page in paginator.paginate(
                Path=prefix,
                Recursive=True,
                WithDecryption=self.decrypt
            ):
                for param in page.get("Parameters", []):
                    # Remove prefix from key name
                    key = param["Name"].replace(prefix, "")
                    result[key] = param["Value"]
            
            return result
        except Exception as e:
            raise ProviderError(f"Failed to get all parameters from AWS SSM: {e}")
    
    def is_available(self) -> bool:
        """Check if AWS SSM is accessible."""
        try:
            self._get_client()
            return True
        except Exception:
            return False

