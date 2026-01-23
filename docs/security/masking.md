# Secret Masking

Automatic detection and masking of secret values.

## Automatic Detection

Secrets are automatically detected for keys containing:
- `secret`
- `key`
- `token`
- `password`
- `pwd`
- `credential`
- `auth`
- `api[_-]?key`

## Masking Behavior

### Safe Representation

```python
config = load_env()

# Safe for logging (secrets masked)
safe = config.safe_repr()
print(safe)
# {"API_KEY": "****1234", "PORT": 8080, "DB_PASSWORD": "****"}
```

### Masking Format

- **Values ≤ 4 chars**: Fully masked (`****`)
- **Values > 4 chars**: Last 4 visible (`****1234`)

### Full Access

```python
# Full access (use with caution)
value = config["API_KEY"]  # Full value, not masked
```

## Custom Secret Patterns

### Mark as Secret

```python
from env_loader_pro.utils import mark_as_secret

config = load_env(
    custom_secrets=[mark_as_secret("CUSTOM_SECRET")]
)
```

### Custom Patterns

```python
from env_loader_pro.utils import is_secret_key

# Check if key is secret
if is_secret_key("MY_API_KEY"):
    print("This is a secret")
```

## Export Safety

### JSON Export

```python
config = load_env()

# Safe export (secrets masked)
config.save("config.json", format="json", safe=True)
```

### YAML Export

```python
# Safe export (secrets masked)
config.save("config.yaml", format="yaml", safe=True)
```

## Logging Safety

### Safe Logging

```python
import logging

config = load_env()

# Safe for logging
logging.info(f"Config: {config.safe_repr()}")
# Secrets are masked
```

### Unsafe Logging

```python
# NEVER do this:
logging.info(f"API Key: {config['API_KEY']}")  # ❌ Exposes secret
```

## Best Practices

1. **Always use `safe_repr()`** for logging
2. **Never log secrets directly**
3. **Use custom patterns** for project-specific secrets
4. **Enable audit trail** to track secret access
5. **Review logs** to ensure no secrets leaked

## Related Topics

- [Security Model](../security/model.md)
- [Audit Trail](../enterprise/audit.md)
