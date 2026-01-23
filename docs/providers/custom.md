# Custom Providers

Create your own provider to load configuration from any source.

## Provider Interface

All providers inherit from `BaseProvider`:

```python
from env_loader_pro.providers import BaseProvider
from typing import Dict, Optional

class CustomProvider(BaseProvider):
    def get(self, key: str) -> Optional[str]:
        """Get single value."""
        pass
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        pass
    
    def get_all(self) -> Dict[str, str]:
        """Get all values (optional, for efficiency)."""
        pass
```

## Example: Database Provider

```python
from env_loader_pro.providers import BaseProvider
from env_loader_pro.exceptions import ProviderError
from typing import Dict, Optional
import sqlite3

class DatabaseProvider(BaseProvider):
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get(self, key: str) -> Optional[str]:
        """Get value from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            raise ProviderError(f"Failed to get {key} from database: {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value:
                result[key] = value
        return result
    
    def get_all(self) -> Dict[str, str]:
        """Get all values from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM config")
            rows = cursor.fetchall()
            conn.close()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            raise ProviderError(f"Failed to get all from database: {e}")
    
    def is_available(self) -> bool:
        """Check if database is available."""
        import os
        return os.path.exists(self.db_path)
```

## Example: HTTP API Provider

```python
import requests
from env_loader_pro.providers import BaseProvider
from env_loader_pro.exceptions import ProviderError

class HTTPProvider(BaseProvider):
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
    
    def get(self, key: str) -> Optional[str]:
        """Get value from HTTP API."""
        try:
            response = requests.get(
                f"{self.api_url}/config/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json().get("value")
        except Exception as e:
            raise ProviderError(f"Failed to get {key} from API: {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value:
                result[key] = value
        return result
    
    def is_available(self) -> bool:
        """Check if API is available."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
```

## Using Custom Provider

```python
from env_loader_pro import load_env

# Create custom provider
custom_provider = CustomProvider(config="...")

# Use with load_env
config = load_env(
    env="prod",
    providers=[custom_provider],
    audit=True
)
```

## Provider Capabilities

Override capabilities if needed:

```python
class CustomProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        # Customize capabilities
        self._capabilities.batch = True
        self._capabilities.cacheable = True
        self._capabilities.rotatable = False
```

## Secret Metadata

Optionally provide secret metadata:

```python
from env_loader_pro.providers import SecretMetadata

class CustomProvider(BaseProvider):
    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for secret."""
        return SecretMetadata(
            ttl=3600,
            rotatable=True,
            expires_at="2024-12-31T23:59:59Z"
        )
```

## Best Practices

1. **Handle errors gracefully** - Raise `ProviderError` on failure
2. **Implement `is_available()`** - Check if provider is accessible
3. **Support `get_all()`** - More efficient than multiple `get()` calls
4. **Set capabilities** - Help loader optimize behavior
5. **Enable caching** - If provider supports it

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Failure Policies](../enterprise/policies.md)
