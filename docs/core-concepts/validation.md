# Validation

env-loader-pro provides multiple validation mechanisms to ensure configuration correctness. Validation happens **after** type casting and **before** returning the configuration.

## Validation Order

Validation is applied in this order:

1. **Required variables** - Check if required variables exist
2. **Empty values** - Check if required variables are empty
3. **Strict mode** - Check for unknown variables
4. **Deprecated variables** - Warn about deprecated variables
5. **Custom validators** - Apply custom validation rules
6. **Regex validators** - Apply regex pattern validation
7. **Policy-as-code** - Apply policy enforcement (if enabled)

## Required Variables

Ensure critical variables are present:

```python
config = load_env(
    required=["API_KEY", "DB_URI", "PORT"]
)
# Raises ValidationError if any required variable is missing
```

### Missing Required Variables

If a required variable is missing, `ValidationError` is raised:

```python
# .env: API_KEY=secret (but DB_URI missing)
config = load_env(required=["API_KEY", "DB_URI", "PORT"])
# Raises: ValidationError: Missing required environment variables: DB_URI, PORT
```

### Empty Required Values

Empty values for required variables also raise an error:

```python
# .env: API_KEY= (empty)
config = load_env(required=["API_KEY"])
# Raises: ValidationError: Required variable 'API_KEY' is empty
```

!!! note "Empty vs Missing"
    - **Missing**: Variable not in config at all → `ValidationError`
    - **Empty**: Variable exists but is `None` or `""` → `ValidationError`

## Validation Rules

Add custom validation logic with lambda functions or callables:

```python
config = load_env(
    types={"PORT": int},
    rules={
        "PORT": lambda v: 1024 < v < 65535,
        "TIMEOUT": lambda v: v > 0,
        "ALLOWED_HOSTS": lambda hosts: len(hosts) > 0
    }
)
# Raises ValidationError if any rule returns False
```

### Rule Function Signature

Validation rules receive the **typed value** (after type casting):

```python
rules = {
    # Integer validation
    "PORT": lambda v: isinstance(v, int) and 1024 < v < 65535,
    
    # String validation
    "EMAIL": lambda v: "@" in v and "." in v.split("@")[1],
    
    # List validation
    "HOSTS": lambda hosts: isinstance(hosts, list) and len(hosts) > 0,
    
    # Complex validation
    "API_KEY": lambda key: len(key) >= 32 and key.startswith("sk-")
}
```

!!! warning "Rule Execution Order"
    Rules are executed **after** type casting. If type casting fails, rules are not executed.

### Rule Error Messages

When a rule fails, `ValidationError` is raised with a descriptive message:

```python
# .env: PORT=80
config = load_env(
    types={"PORT": int},
    rules={"PORT": lambda v: 1024 < v < 65535}
)
# Raises: ValidationError: Custom validation failed for 'PORT': 80
```

### Handling Rule Exceptions

If a rule raises an exception, it's wrapped in `ValidationError`:

```python
def validate_port(v):
    if not isinstance(v, int):
        raise TypeError("Port must be an integer")
    return 1024 < v < 65535

config = load_env(
    types={"PORT": int},
    rules={"PORT": validate_port}
)
# If TypeError raised, wrapped as: ValidationError: Validation error for 'PORT': Port must be an integer
```

## Strict Mode

Enable strict mode to catch unknown variables (typos, etc.):

```python
config = load_env(
    required=["API_KEY"],
    types={"PORT": int},
    strict=True
)
# Warns about variables in .env not in required/types/defaults
```

### Strict Mode Behavior

- **Warns** (does not fail) about unknown variables by default
- Useful for catching typos in variable names
- Recommended for production environments

```python
# .env: API_KEY=secret, PORT=8080, TYPO_VAR=value
config = load_env(
    required=["API_KEY"],
    types={"PORT": int},
    strict=True
)
# Warning: Unknown variables found: TYPO_VAR
```

!!! note "Strict Mode Default"
    By default, strict mode **warns** instead of failing. This can be changed in `SchemaValidator` initialization.

## Regex Validators

Validate format with regex patterns:

```python
import re

config = load_env(
    regex_validators={
        "EMAIL": r'^[\w\.-]+@[\w\.-]+\.\w+$',
        "VERSION": r'^\d+\.\d+\.\d+$',
        "IP_ADDRESS": r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    }
)
# Raises ValidationError if pattern doesn't match
```

### Regex Validation Behavior

- Patterns are compiled once and reused
- Validation happens after type casting
- Empty values are **not** validated (use required check instead)

```python
# .env: EMAIL=invalid-email
config = load_env(
    regex_validators={"EMAIL": r'^[\w\.-]+@[\w\.-]+\.\w+$'}
)
# Raises: ValidationError: Regex validation failed for 'EMAIL': invalid-email
```

## Deprecated Variables

Warn about deprecated variables:

```python
config = load_env(
    deprecated_vars=["OLD_API_KEY", "LEGACY_PORT"]
)
# Warns: Variable 'OLD_API_KEY' is deprecated and will be removed in a future version
```

!!! tip "Deprecation Strategy"
    Use deprecated variables to provide migration paths:
    1. Mark old variable as deprecated
    2. Support both old and new variables
    3. Remove old variable in next major version

## Schema Validation

Use Pydantic or dataclass for comprehensive validation:

```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel, validator

class Config(BaseModel):
    port: int
    email: str
    
    @validator('port')
    def validate_port(cls, v):
        if not 1024 < v < 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

config = load_with_schema(Config)
# Pydantic validates all fields
```

## Policy-as-Code Validation

Enforce policies via JSON/YAML files:

```yaml
# policy.yaml
require:
  - API_KEY
  - DB_PASSWORD
forbid:
  - DEBUG
```

```python
config = load_env(policy="policy.yaml")
# Fails if policy violated
```

See [Policy-as-Code](../enterprise/policy-as-code.md) for details.

## Validation Error Messages

Clear error messages help debugging:

```python
try:
    config = load_env(required=["API_KEY"])
except ValidationError as e:
    print(e)
    # "Missing required environment variables: API_KEY"
```

### Error Message Format

| Error Type | Message Format |
|------------|----------------|
| Missing required | `"Missing required environment variables: VAR1, VAR2"` |
| Empty required | `"Required variable 'VAR' is empty"` |
| Custom validation | `"Custom validation failed for 'VAR': value"` |
| Regex validation | `"Regex validation failed for 'VAR': value"` |
| Unknown variables | `"Unknown variables found: VAR1, VAR2"` |

## Best Practices

### 1. Validate Early

Check required variables at startup:

```python
# Application startup
config = load_env(
    required=["API_KEY", "DB_URI"],
    types={"PORT": int},
    rules={"PORT": lambda v: 1024 < v < 65535}
)
# Fail fast if configuration is invalid
```

### 2. Use Strict Mode in Production

Enable strict mode to catch typos:

```python
config = load_env(
    env="prod",
    strict=True,  # Catch unknown variables
    required=["API_KEY"]
)
```

### 3. Combine Validation Methods

Use multiple validation methods for comprehensive checks:

```python
config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "EMAIL": str},
    rules={"PORT": lambda v: 1024 < v < 65535},
    regex_validators={"EMAIL": r'^[\w\.-]+@[\w\.-]+\.\w+$'},
    strict=True
)
```

### 4. Use Schemas for Complex Validation

For complex validation, use Pydantic schemas:

```python
# Better than multiple rules
config = load_with_schema(Config)
```

### 5. Handle Validation Errors Gracefully

```python
try:
    config = load_env(required=["API_KEY"])
except ValidationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
```

## Common Mistakes

### Mistake 1: Validating Before Type Casting

```python
# ❌ WRONG: Rule receives string
rules={"PORT": lambda v: 1024 < int(v) < 65535}

# ✅ CORRECT: Rule receives typed value
types={"PORT": int}
rules={"PORT": lambda v: 1024 < v < 65535}
```

### Mistake 2: Not Handling Empty Values

```python
# ❌ WRONG: Empty string passes validation
rules={"API_KEY": lambda v: len(v) > 0}

# ✅ CORRECT: Use required check
required=["API_KEY"]
```

### Mistake 3: Strict Mode Failing

```python
# ❌ WRONG: Strict mode fails on unknown vars
config = load_env(strict=True)  # Fails if any unknown vars

# ✅ CORRECT: Strict mode warns by default
# Or use warn_only=False to make it fail
```

## Related Topics

- [Schema Support](../core-concepts/schema.md) - Type-safe validation
- [Policy-as-Code](../enterprise/policy-as-code.md) - Policy enforcement
- [Security Model](../security/model.md) - Security validation
