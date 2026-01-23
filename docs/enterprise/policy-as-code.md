# Policy-as-Code

Enforce configuration policies via JSON/YAML files.

## Overview

Policy-as-code allows you to define and enforce configuration rules:

- Require specific variables
- Forbid certain variables
- Enforce source requirements
- Set TTL requirements

## Policy File Format

### YAML

```yaml
# policy.yaml
require:
  - API_KEY
  - DB_PASSWORD
  - PORT

forbid:
  - DEBUG
  - TEST_MODE

sources:
  API_KEY: azure
  DB_PASSWORD: azure

ttl:
  API_KEY: 3600
  DB_PASSWORD: 7200

provider_failure_policy:
  azure: fail
  aws: fallback
```

### JSON

```json
{
  "require": ["API_KEY", "DB_PASSWORD", "PORT"],
  "forbid": ["DEBUG", "TEST_MODE"],
  "sources": {
    "API_KEY": "azure",
    "DB_PASSWORD": "azure"
  },
  "ttl": {
    "API_KEY": 3600,
    "DB_PASSWORD": 7200
  },
  "provider_failure_policy": {
    "azure": "fail",
    "aws": "fallback"
  }
}
```

## Using Policies

### Load with Policy

```python
from env_loader_pro import load_env

config = load_env(
    env="prod",
    policy="policy.yaml"  # Enforces policy
)
# Fails if policy violated
```

### Policy Rules

#### Require Variables

```yaml
require:
  - API_KEY
  - DB_PASSWORD
```

Fails if any required variable is missing.

#### Forbid Variables

```yaml
forbid:
  - DEBUG
  - TEST_MODE
```

Fails if any forbidden variable is present.

#### Source Requirements

```yaml
sources:
  API_KEY: azure
  DB_PASSWORD: azure
```

Requires variables to come from specific sources.

#### TTL Requirements

```yaml
ttl:
  API_KEY: 3600
  DB_PASSWORD: 7200
```

Requires secrets to have TTL less than specified (in seconds).

#### Failure Policies

```yaml
provider_failure_policy:
  azure: fail
  aws: fallback
```

Sets failure policies per provider.

## Policy Validation

### Missing Required Variable

```python
# policy.yaml requires API_KEY
# But API_KEY not in config

config = load_env(policy="policy.yaml")
# Raises PolicyError: Missing required variable: API_KEY
```

### Forbidden Variable Present

```python
# policy.yaml forbids DEBUG
# But DEBUG in config

config = load_env(policy="policy.yaml")
# Raises PolicyError: Forbidden variable present: DEBUG
```

### Source Mismatch

```python
# policy.yaml requires API_KEY from azure
# But API_KEY comes from file

config = load_env(policy="policy.yaml")
# Raises PolicyError: API_KEY must come from azure, got file
```

## Example: Production Policy

```yaml
# policy.prod.yaml
require:
  - API_KEY
  - DB_PASSWORD
  - DB_HOST

forbid:
  - DEBUG
  - TEST_MODE
  - DEV_MODE

sources:
  API_KEY: azure
  DB_PASSWORD: azure

provider_failure_policy:
  azure: fail
```

```python
config = load_env(
    env="prod",
    policy="policy.prod.yaml"
)
```

## Example: Development Policy

```yaml
# policy.dev.yaml
require:
  - API_KEY

forbid: []  # Allow anything

provider_failure_policy:
  azure: warn  # Warn but continue
```

```python
config = load_env(
    env="dev",
    policy="policy.dev.yaml"
)
```

## Best Practices

1. **Use different policies per environment**
2. **Require secrets from secure sources** in production
3. **Forbid debug flags** in production
4. **Set TTL requirements** for secrets
5. **Version control policies** (without secrets)

## Related Topics

- [Failure Policies](../enterprise/policies.md)
- [Security Model](../security/model.md)
