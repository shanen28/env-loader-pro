# Configuration Diff

Compare configurations to detect drift and changes.

## Overview

Configuration diff allows you to:

- Compare current vs. baseline config
- Detect added/removed variables
- Detect secret changes
- Prevent accidental exposure

## Basic Usage

```python
from env_loader_pro import load_env, diff_configs

# Load current config
current = load_env(env="prod")

# Load baseline (from file or previous run)
baseline = load_env(path=".env.baseline")

# Compare
diff = diff_configs(current, baseline)

# Check for changes
if diff.has_changes():
    print("Configuration changed!")
    print(f"Added: {diff.added}")
    print(f"Removed: {diff.removed}")
    print(f"Changed: {diff.changed}")
```

## Diff Results

### Added Variables

```python
diff = diff_configs(current, baseline)

if diff.added:
    print(f"New variables: {diff.added}")
    # {"NEW_VAR": "value"}
```

### Removed Variables

```python
if diff.removed:
    print(f"Removed variables: {diff.removed}")
    # {"OLD_VAR": "value"}
```

### Changed Variables

```python
if diff.changed:
    print(f"Changed variables: {diff.changed}")
    # {"VAR": {"old": "old_value", "new": "new_value"}}
```

### Secret Changes

```python
if diff.has_secret_changes():
    print(f"Secret changes detected!")
    print(f"Added secrets: {diff.added_secrets}")
    print(f"Removed secrets: {diff.removed_secrets}")
    print(f"Changed secrets: {diff.changed_secrets}")
```

## CLI Usage

### Basic Diff

```bash
# Compare current vs. baseline
envloader diff --baseline .env.baseline
```

### CI-Safe Diff

```bash
# No cloud access required
envloader diff --ci --baseline .env.baseline
```

### Deny Secret Changes

```bash
# Fail if secrets added/removed
envloader diff --ci --deny-secret-changes --baseline .env.baseline
```

### Deny Added Secrets

```bash
# Fail if new secrets added
envloader diff --ci --deny-added-secrets --baseline .env.baseline
```

## Use Cases

### Prevent Secret Exposure

```bash
# In CI/CD pipeline
envloader diff --ci --deny-secret-changes --baseline .env.baseline

# Fails if secrets added/removed/changed
```

### Configuration Drift Detection

```python
# Load baseline from previous deployment
baseline = load_env(path=".env.prod.baseline")

# Load current
current = load_env(env="prod")

# Compare
diff = diff_configs(current, baseline)

if diff.has_changes():
    # Alert on drift
    send_alert(f"Configuration drift detected: {diff.changed}")
```

### Audit Configuration Changes

```python
# Save baseline
baseline = load_env(env="prod")
baseline.save(".env.prod.baseline", format="json")

# Later, compare
current = load_env(env="prod")
diff = diff_configs(current, baseline)

# Log changes
log_audit(diff.to_dict())
```

## Best Practices

1. **Store baselines** for each environment
2. **Use in CI/CD** to prevent accidental changes
3. **Deny secret changes** in production
4. **Alert on drift** for critical configs
5. **Review changes** before deployment

## Related Topics

- [Security Model](../security/model.md)
- [Audit Trail](../enterprise/audit.md)
