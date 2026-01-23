# Providers API

Provider classes and interfaces.

## BaseProvider

Abstract base class for all providers.

```python
from env_loader_pro.providers import BaseProvider

class CustomProvider(BaseProvider):
    def get(self, key: str) -> Optional[str]:
        pass
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        pass
```

## AzureKeyVaultProvider

```python
from env_loader_pro.providers import AzureKeyVaultProvider

provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net",
    credential=None,  # Uses DefaultAzureCredential
    cache=True,
    cache_ttl=3600
)
```

## AWSSecretsManagerProvider

```python
from env_loader_pro.providers import AWSSecretsManagerProvider

provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod",
    region="us-east-1",
    cache=True,
    cache_ttl=3600
)
```

## AWSSSMProvider

```python
from env_loader_pro.providers import AWSSSMProvider

provider = AWSSSMProvider(
    prefix="/myapp/prod/",
    region="us-east-1"
)
```

## Related Topics

- [Providers Overview](../providers/overview.md)
