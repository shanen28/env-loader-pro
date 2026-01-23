# Providers Overview

Providers allow loading configuration from external sources like cloud secret managers, filesystems, and custom backends. This document explains the provider system, how it works, and how to use it.

## What Are Providers?

Providers are **pluggable backends** that fetch configuration values from external sources. They abstract away the complexity of different secret management systems, providing a unified interface for loading configuration.

### Why Providers?

**Problem**: Configuration can come from many sources:
- Azure Key Vault
- AWS Secrets Manager
- Kubernetes secrets
- Docker secrets
- Local `.env` files
- System environment variables

**Solution**: Provider abstraction that:
- Unifies different sources
- Handles authentication automatically
- Supports caching and error handling
- Provides consistent interface

## Supported Providers

### Cloud Providers

- **Azure Key Vault** - Azure cloud secrets (`env-loader-pro[azure]`)
- **AWS Secrets Manager** - AWS cloud secrets (`env-loader-pro[aws]`)
- **AWS SSM Parameter Store** - AWS parameter store (`env-loader-pro[aws]`)

### Container Providers

- **Docker Secrets** - Docker mounted secrets (`/run/secrets/*`)
- **Kubernetes Secrets** - K8s mounted secrets/configmaps (`/var/run/secrets/kubernetes.io/serviceaccount/*`)

### Filesystem Providers

- **Filesystem** - Filesystem-mounted configs (automatic)

### Custom Providers

- **Custom** - Build your own provider (see [Custom Providers](../providers/custom.md))

## Provider Priority

Providers have the **highest priority** in configuration precedence:

1. **Cloud providers** (Azure, AWS) - Highest priority
2. System environment variables
3. Docker/K8s secrets
4. `.env.{env}` files (environment-specific)
5. Base `.env` file
6. Schema defaults - Lowest priority

**Why this order?**
- **Security**: Cloud secrets should always win (secrets win)
- **Predictability**: Fixed order, no ambiguity
- **Production-first**: Production secrets override local files

## Basic Usage

### Single Provider

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AzureKeyVaultProvider

# Create provider
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net"
)

# Use with load_env
config = load_env(
    env="prod",
    providers=[provider]
)

# Secrets from Azure override .env files
db_password = config["DB_PASSWORD"]  # From Azure
```

### Multiple Providers

```python
from env_loader_pro.providers import (
    AzureKeyVaultProvider,
    AWSSecretsManagerProvider
)

# Use multiple providers
config = load_env(
    providers=[
        AzureKeyVaultProvider(...),      # Loaded first
        AWSSecretsManagerProvider(...)   # Overrides Azure if same key
    ]
)
# Later providers override earlier ones
```

**Use case**: Use Azure for secrets, AWS for configuration.

## Provider Interface

All providers implement the `BaseProvider` interface:

```python
from env_loader_pro.providers import BaseProvider

class CustomProvider(BaseProvider):
    def get(self, key: str) -> Optional[str]:
        """Get single value."""
        pass
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values (batch operation)."""
        pass
    
    def get_all(self) -> Dict[str, str]:
        """Get all values (optional, for efficiency)."""
        pass
```

### Required Methods

- `get(key: str) -> Optional[str]` - Get single value
- `get_many(keys: list[str]) -> Dict[str, str]` - Get multiple values (if `capabilities.batch` is True)

### Optional Methods

- `get_all() -> Dict[str, str]` - Get all values (for efficiency)

## Provider Capabilities

Each provider exposes capabilities that describe what it can do:

```python
provider = AzureKeyVaultProvider(...)
capabilities = provider.capabilities

# {
#   "batch": True,        # Supports get_many (batch operations)
#   "cacheable": True,    # Values can be cached
#   "rotatable": False,   # Supports secret rotation
#   "watchable": False,   # Supports watching for changes
#   "metadata": True      # Provides secret metadata (TTL, etc.)
# }
```

### Capability Flags

- **`batch`**: Provider supports batch operations (`get_many`)
- **`cacheable`**: Values can be cached (safe to cache)
- **`rotatable`**: Provider supports secret rotation
- **`watchable`**: Provider supports watching for changes
- **`metadata`**: Provider provides metadata (TTL, rotation status, etc.)

### Using Capabilities

```python
provider = AzureKeyVaultProvider(...)

if provider.capabilities.batch:
    # Use batch operation for efficiency
    values = provider.get_many(["KEY1", "KEY2", "KEY3"])
else:
    # Fall back to individual calls
    values = {k: provider.get(k) for k in ["KEY1", "KEY2", "KEY3"]}
```

## Failure Policies

Control how provider errors are handled:

```python
config = load_env(
    providers=[azure_provider],
    failure_policy={
        "azure": "fail",      # Raise error (production)
        "aws": "fallback",    # Silently continue (optional)
        "filesystem": "warn"  # Log warning (development)
    }
)
```

**Policies:**
- `fail` - Raise error immediately (production)
- `warn` - Log warning and continue (development)
- `fallback` - Silently continue (resilient)

See [Failure Policies](../enterprise/policies.md) for details.

## Caching

Providers support caching to reduce API calls:

```python
config = load_env(
    providers=[azure_provider],
    cache=True,
    cache_ttl=3600  # 1 hour
)
```

**Benefits:**
- Reduced API calls (cost savings)
- Faster loading (cached values)
- Rate limit protection

**Tradeoffs:**
- Stale values (if secrets rotate)
- Memory usage (cached values)

**Best practice**: Use caching with appropriate TTL based on secret rotation frequency.

## Availability Check

Check if provider is available before using:

```python
provider = AzureKeyVaultProvider(...)

if provider.is_available():
    # Provider is accessible
    config = load_env(providers=[provider])
else:
    # Fallback to local config
    config = load_env()
```

**Use case**: Graceful degradation when cloud providers are unavailable.

## Authentication

### Azure Key Vault

Uses `DefaultAzureCredential` which supports:
- Managed Identity (Azure VMs, App Service, Functions)
- Service Principal (Client ID/Secret)
- Azure CLI (local development)
- Environment Variables (Client credentials)

### AWS Providers

Uses boto3 default credential chain:
- IAM Role (EC2, ECS, Lambda)
- Environment Variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS Credentials File (`~/.aws/credentials`)
- IAM Instance Profile (EC2)

### Docker/Kubernetes

Uses filesystem mounts (no authentication needed):
- Docker: `/run/secrets/*`
- Kubernetes: `/var/run/secrets/kubernetes.io/serviceaccount/*`

## Provider Lifecycle

### Initialization

```python
# Provider created
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net"
)
# No network calls yet
```

### Loading

```python
# Provider used in load_env
config = load_env(providers=[provider])
# Network calls happen here
# Values cached if cache=True
```

### Caching

```python
# Subsequent loads use cache
config = load_env(providers=[provider], cache=True)
# Uses cached values if TTL not expired
```

## Error Handling

### Network Errors

```python
try:
    config = load_env(providers=[azure_provider])
except ProviderError as e:
    # Handle provider error
    logger.error(f"Provider error: {e}")
    # Fallback to local config
    config = load_env()
```

### Authentication Errors

```python
try:
    config = load_env(providers=[azure_provider])
except AuthenticationError as e:
    # Handle authentication error
    logger.error(f"Authentication failed: {e}")
    sys.exit(1)
```

### Rate Limit Errors

```python
try:
    config = load_env(providers=[azure_provider])
except RateLimitError as e:
    # Handle rate limit
    logger.warning(f"Rate limit: {e}")
    # Use cached values or retry
    time.sleep(60)
    config = load_env(providers=[azure_provider])
```

## Best Practices

### 1. Use Cloud Providers for Secrets

```python
# ✅ GOOD: Secrets from cloud
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}
)

# ❌ BAD: Secrets in .env files
# .env: DB_PASSWORD=secret123  # Don't do this!
```

### 2. Set Failure Policies

```python
# ✅ GOOD: Explicit failure policy
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Explicit
)

# ❌ BAD: Default behavior (might not be what you want)
config = load_env(providers=[azure_provider])  # Uses defaults
```

### 3. Enable Caching

```python
# ✅ GOOD: Caching enabled
config = load_env(
    providers=[azure_provider],
    cache=True,
    cache_ttl=3600
)

# ❌ BAD: No caching (expensive)
config = load_env(providers=[azure_provider])  # No cache
```

### 4. Use Batch Operations

```python
# ✅ GOOD: Batch operation
if provider.capabilities.batch:
    values = provider.get_many(["KEY1", "KEY2", "KEY3"])

# ❌ BAD: Individual calls
values = {k: provider.get(k) for k in ["KEY1", "KEY2", "KEY3"]}
```

### 5. Handle Errors Gracefully

```python
# ✅ GOOD: Error handling
try:
    config = load_env(providers=[azure_provider])
except ProviderError:
    config = load_env()  # Fallback

# ❌ BAD: No error handling
config = load_env(providers=[azure_provider])  # Might crash
```

## Common Mistakes

### Mistake 1: Not Setting Failure Policies

```python
# ❌ WRONG: Uses defaults, might not be what you want
config = load_env(providers=[azure_provider])

# ✅ CORRECT: Explicit failure policy
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}
)
```

### Mistake 2: Not Using Caching

```python
# ❌ WRONG: No caching (expensive API calls)
config = load_env(providers=[azure_provider])

# ✅ CORRECT: Caching enabled
config = load_env(
    providers=[azure_provider],
    cache=True,
    cache_ttl=3600
)
```

### Mistake 3: Not Handling Errors

```python
# ❌ WRONG: No error handling
config = load_env(providers=[azure_provider])

# ✅ CORRECT: Error handling
try:
    config = load_env(providers=[azure_provider])
except ProviderError:
    config = load_env()  # Fallback
```

## Related Topics

- [Azure Key Vault](../providers/azure.md) - Azure integration
- [AWS Secrets Manager](../providers/aws.md) - AWS integration
- [Docker & Kubernetes](../providers/docker-k8s.md) - Container secrets
- [Custom Providers](../providers/custom.md) - Build your own
- [Failure Policies](../enterprise/policies.md) - Error handling
- [Provider System](../architecture/providers.md) - Architecture details