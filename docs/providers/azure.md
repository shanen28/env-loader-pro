# Azure Key Vault Provider

Load secrets from Azure Key Vault with automatic authentication.

## Installation

```bash
pip install env-loader-pro[azure]
```

## Basic Usage

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AzureKeyVaultProvider

# Create provider
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net"
)

# Load configuration
config = load_env(
    env="prod",
    providers=[provider]
)
```

## Authentication

Uses `DefaultAzureCredential` which supports:

- **Managed Identity** - Azure VMs, App Service, Functions
- **Service Principal** - Client ID/Secret
- **Azure CLI** - Local development
- **Environment Variables** - Client credentials

### Custom Credential

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="...",
    client_id="...",
    client_secret="..."
)

provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net",
    credential=credential
)
```

## Caching

Enable caching to reduce API calls:

```python
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net",
    cache=True,
    cache_ttl=3600  # 1 hour
)
```

## Failure Policy

```python
config = load_env(
    providers=[provider],
    failure_policy={
        "azure": "fail"  # Raise error if Azure unavailable
    }
)
```

## Example

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AzureKeyVaultProvider

# Production setup
provider = AzureKeyVaultProvider(
    vault_url="https://prod-vault.vault.azure.net"
)

config = load_env(
    env="prod",
    providers=[provider],
    audit=True,  # Track provenance
    cache=True,
    cache_ttl=3600
)

# Secrets from Azure override local .env
db_password = config["DB_PASSWORD"]  # From Azure Key Vault
```

## Capabilities

```python
provider = AzureKeyVaultProvider(...)
print(provider.capabilities.to_dict())

# {
#   "batch": True,
#   "cacheable": True,
#   "rotatable": True,
#   "watchable": False,
#   "metadata": True
# }
```

## Best Practices

1. **Use Managed Identity** in production
2. **Enable caching** to reduce API calls
3. **Set failure policy** to "fail" in production
4. **Enable audit** to track secret access
5. **Use environment-specific vaults** per environment

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Failure Policies](../enterprise/policies.md)
- [Audit Trail](../enterprise/audit.md)
