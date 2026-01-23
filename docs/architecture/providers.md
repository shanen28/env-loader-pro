# Provider System

How the provider plugin system works.

## Provider Interface

All providers inherit from `BaseProvider`:

```python
from env_loader_pro.providers import BaseProvider

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

## Provider Capabilities

Each provider exposes capabilities:

```python
provider = AzureKeyVaultProvider(...)
capabilities = provider.capabilities

# {
#   "batch": True,        # Supports get_many
#   "cacheable": True,    # Values can be cached
#   "rotatable": False,   # Supports secret rotation
#   "watchable": False,   # Supports watching
#   "metadata": True      # Provides secret metadata
# }
```

## Provider Priority

Providers have the **highest priority** in configuration precedence.

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Custom Providers](../providers/custom.md)
