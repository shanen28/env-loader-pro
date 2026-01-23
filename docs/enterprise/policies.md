# Failure Policies

Control how the loader handles errors from different configuration sources. Failure policies allow you to specify **explicit behavior** for each provider, ensuring predictable behavior in production while maintaining resilience in development.

## Why Explicit Failure Policies?

### Problem

When a cloud provider fails (network outage, authentication error, rate limit), what should happen?

- **Fail fast?** - Application crashes, but you know immediately
- **Silently continue?** - Application runs, but might be misconfigured
- **Log and continue?** - Application runs, but with warnings

Different environments need different behaviors. Production should fail fast. Development should be resilient.

### Decision

**Explicit per-provider failure policies** with three options:

- `fail` - Raise error immediately (production)
- `warn` - Log warning and continue (development)
- `fallback` - Silently continue (resilient)

## Policy Options

### Fail (Production)

**Behavior**: Raises `ProviderError` immediately when provider fails.

```python
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}
)

# If Azure Key Vault is unavailable:
# Raises: ProviderError: Provider azure error: Connection timeout
```

**When to use:**
- Production environments
- Critical providers (secrets must come from secure source)
- When misconfiguration is worse than failure

**Example scenario:**
```python
# Production: secrets must come from Azure
config = load_env(
    env="prod",
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Fail if Azure unavailable
)
# Application won't start with wrong secrets
```

### Warn (Development)

**Behavior**: Logs warning message and continues loading from other sources.

```python
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "warn"}
)

# If Azure Key Vault is unavailable:
# WARNING: Provider azure error: Connection timeout
# Continues loading from .env files
```

**When to use:**
- Development environments
- Optional providers (nice to have, not required)
- When you want visibility but not failure

**Example scenario:**
```python
# Development: Azure optional, use .env if unavailable
config = load_env(
    env="dev",
    providers=[azure_provider],
    failure_policy={"azure": "warn"}  # Warn but continue
)
# Application runs with .env values, but logs warning
```

### Fallback (Resilient)

**Behavior**: Silently continues, no error or warning.

```python
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fallback"}
)

# If Azure Key Vault is unavailable:
# Silently continues, uses .env files
# No error, no warning
```

**When to use:**
- Resilient systems (must work even if providers unavailable)
- Optional providers (completely optional)
- When failures are expected and handled elsewhere

**Example scenario:**
```python
# Resilient: must work even if cloud unavailable
config = load_env(
    providers=[azure_provider, aws_provider],
    failure_policy={
        "azure": "fallback",  # Silently continue
        "aws": "fallback"     # Silently continue
    }
)
# Application always starts, uses .env if cloud unavailable
```

## Multiple Providers

You can set different policies for different providers:

```python
config = load_env(
    providers=[azure_provider, aws_provider, filesystem_provider],
    failure_policy={
        "azure": "fail",      # Critical in production
        "aws": "fallback",    # Optional
        "filesystem": "warn"  # Development only
    }
)
```

**Priority**: Later providers override earlier ones if they have the same keys.

## Default Policies

If no policy is specified, defaults are used:

```python
# Default policies
{
    "azure": "fail",        # Production: fail on error
    "aws": "fallback",      # Fallback if unavailable
    "filesystem": "warn",   # Warn on filesystem errors
    "docker": "warn",       # Warn on Docker secret errors
    "kubernetes": "warn"    # Warn on K8s errors
}
```

You can override defaults:

```python
# Override defaults
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "warn"}  # Override default "fail"
)
```

## Policy Resolution

Policies are matched by provider name:

1. **Exact match**: `"azure"` matches `AzureKeyVaultProvider`
2. **Partial match**: `"azure"` matches `"AzureKeyVaultProvider"` (case-insensitive)
3. **Default**: If no match, uses default policy

```python
# These all match AzureKeyVaultProvider:
failure_policy = {
    "azure": "fail",
    "AzureKeyVaultProvider": "fail",
    "Azure": "fail"
}
```

## Real-World Scenarios

### Scenario 1: Production Deployment

**Requirement**: Secrets must come from Azure Key Vault. Application should not start if Azure is unavailable.

```python
config = load_env(
    env="prod",
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Fail fast
)
# Application won't start with wrong secrets
```

### Scenario 2: Development Environment

**Requirement**: Use Azure if available, but fall back to `.env` file for local development.

```python
config = load_env(
    env="dev",
    providers=[azure_provider],
    failure_policy={"azure": "warn"}  # Warn but continue
)
# Application runs with .env, logs warning about Azure
```

### Scenario 3: Resilient System

**Requirement**: Application must start even if all cloud providers are unavailable.

```python
config = load_env(
    providers=[azure_provider, aws_provider],
    failure_policy={
        "azure": "fallback",  # Silently continue
        "aws": "fallback"     # Silently continue
    }
)
# Application always starts, uses .env if cloud unavailable
```

### Scenario 4: Multi-Provider Setup

**Requirement**: Azure is critical, AWS is optional, filesystem is for development.

```python
config = load_env(
    providers=[azure_provider, aws_provider, filesystem_provider],
    failure_policy={
        "azure": "fail",      # Critical: fail if unavailable
        "aws": "fallback",    # Optional: silently continue
        "filesystem": "warn"  # Development: warn but continue
    }
)
```

## Error Handling

### Fail Policy

```python
try:
    config = load_env(
        providers=[azure_provider],
        failure_policy={"azure": "fail"}
    )
except ProviderError as e:
    logger.error(f"Provider error: {e}")
    # Handle error (alert, retry, etc.)
    sys.exit(1)
```

### Warn Policy

```python
# Warning logged, but continues
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "warn"}
)
# No exception raised
# Check logs for warnings
```

### Fallback Policy

```python
# Silently continues
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fallback"}
)
# No exception, no warning
# Application continues with fallback values
```

## Best Practices

### 1. Use "fail" in Production

```python
# Production: fail fast on critical providers
config = load_env(
    env="prod",
    providers=[azure_provider],
    failure_policy={"azure": "fail"}
)
```

### 2. Use "warn" in Development

```python
# Development: warn but continue
config = load_env(
    env="dev",
    providers=[azure_provider],
    failure_policy={"azure": "warn"}
)
```

### 3. Use "fallback" for Resilience

```python
# Resilient: must work even if providers unavailable
config = load_env(
    providers=[optional_provider],
    failure_policy={"optional_provider": "fallback"}
)
```

### 4. Document Policies

```python
# Document why each policy is set
failure_policy = {
    "azure": "fail",      # Critical: secrets must come from Azure
    "aws": "fallback",    # Optional: can use .env if AWS unavailable
    "filesystem": "warn"  # Development: warn about filesystem usage
}
```

### 5. Environment-Specific Policies

```python
import os

env = os.getenv("ENVIRONMENT", "dev")
policies = {
    "prod": {"azure": "fail", "aws": "fail"},
    "dev": {"azure": "warn", "aws": "fallback"},
    "test": {"azure": "fallback", "aws": "fallback"}
}

config = load_env(
    env=env,
    providers=[azure_provider, aws_provider],
    failure_policy=policies.get(env, {})
)
```

## Common Mistakes

### Mistake 1: Using "fallback" in Production

```python
# ❌ WRONG: Silent failures in production
config = load_env(
    env="prod",
    providers=[azure_provider],
    failure_policy={"azure": "fallback"}  # Bad!
)
# Application might start with wrong secrets

# ✅ CORRECT: Fail fast in production
config = load_env(
    env="prod",
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Good!
)
```

### Mistake 2: Using "fail" in Development

```python
# ❌ WRONG: Fails in development when Azure unavailable
config = load_env(
    env="dev",
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Bad for dev!
)
# Can't develop locally without Azure access

# ✅ CORRECT: Warn in development
config = load_env(
    env="dev",
    providers=[azure_provider],
    failure_policy={"azure": "warn"}  # Good for dev!
)
```

### Mistake 3: Not Setting Policies

```python
# ❌ WRONG: Uses defaults, might not be what you want
config = load_env(providers=[azure_provider])

# ✅ CORRECT: Explicit policies
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Explicit
)
```

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Policy-as-Code](../enterprise/policy-as-code.md)
- [Design Decisions](../architecture/design-decisions.md)