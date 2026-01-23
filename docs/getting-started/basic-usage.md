# Basic Usage

Learn the fundamentals of using env-loader-pro with detailed examples and edge cases.

## Loading Configuration

### Simple Load

The most basic usage loads configuration from a `.env` file:

```python
from env_loader_pro import load_env

# Load from .env file (default path)
config = load_env()

# Access values as strings
port = config["PORT"]  # String: "8080"
```

!!! note "Default Behavior"
    By default, `load_env()`:
    - Loads from `.env` in the current directory
    - Treats all values as strings
    - Expands `${VAR}` syntax
    - Masks secrets in `safe_repr()`

### With Type Casting

Specify types to automatically cast string values:

```python
config = load_env(
    types={
        "PORT": int,
        "DEBUG": bool,
        "TIMEOUT": float
    }
)

port = config["PORT"]      # int: 8080
debug = config["DEBUG"]     # bool: True
timeout = config["TIMEOUT"] # float: 30.5
```

!!! warning "Type Casting Errors"
    If a value cannot be cast to the specified type, `EnvLoaderError` is raised:
    ```python
    # .env: PORT=not-a-number
    config = load_env(types={"PORT": int})
    # Raises: EnvLoaderError: Failed to cast env value 'not-a-number' to int
    ```

### With Required Variables

Ensure critical variables are present:

```python
config = load_env(
    required=["API_KEY", "DB_URI", "PORT"]
)
# Raises EnvLoaderError if any required variable is missing
```

!!! tip "Required vs Optional"
    - `required`: Variables that must exist (raises error if missing)
    - `optional`: Variables that may exist (for documentation only, no validation)

### With Default Values

Provide fallback values for missing variables:

```python
config = load_env(
    defaults={
        "PORT": 8080,
        "DEBUG": False,
        "TIMEOUT": 30
    }
)
# Uses defaults if variables not set in .env or system
```

!!! note "Default Priority"
    Defaults have the **lowest priority** in the precedence order. They are only used if:
    1. Variable is not in cloud providers
    2. Variable is not in system environment
    3. Variable is not in Docker/K8s secrets
    4. Variable is not in .env files

## Environment-Specific Files

Use different configuration files per environment:

```bash
# File structure
.env          # Base configuration (shared)
.env.dev      # Development overrides
.env.prod     # Production overrides
.env.staging  # Staging overrides
```

```python
# Load production config
config = load_env(env="prod")
# Loads .env.prod first, then merges with .env
# .env.prod values override .env values
```

### How Environment Files Work

1. **Base `.env`** is loaded first (if exists)
2. **`.env.{env}`** is loaded second (if exists)
3. **`.env.{env}` values override** base `.env` values
4. **System environment** overrides both
5. **Cloud providers** override everything

```bash
# .env
PORT=8080
DEBUG=false
LOG_LEVEL=info

# .env.prod
PORT=9000
DEBUG=false
```

```python
config = load_env(env="prod")
print(config["PORT"])      # 9000 (from .env.prod)
print(config["DEBUG"])     # false (from .env.prod)
print(config["LOG_LEVEL"]) # info (from .env, .env.prod doesn't override)
```

## Variable Expansion

Expand variables using `${VAR}` syntax:

```bash
# .env file
BASE_URL=https://example.com
API_ENDPOINT=${BASE_URL}/api
FULL_URL=${API_ENDPOINT}/v1
```

```python
config = load_env()

print(config["FULL_URL"])
# Output: https://example.com/api/v1
```

### Nested Expansion

Variables can reference other variables:

```bash
# .env
DOMAIN=example.com
PROTOCOL=https
BASE_URL=${PROTOCOL}://${DOMAIN}
API_URL=${BASE_URL}/api
```

```python
config = load_env()
print(config["API_URL"])  # https://example.com/api
```

### Cycle Detection

Circular references are detected and raise an error:

```bash
# .env
VAR_A=${VAR_B}
VAR_B=${VAR_A}
```

```python
config = load_env()
# Raises: EnvLoaderError: Circular reference detected for variable: VAR_A
```

!!! warning "Expansion Order"
    Variable expansion happens **after** all sources are merged. This means:
    - System environment variables can be referenced
    - Cloud provider values can be referenced
    - Expansion happens in a single pass with cycle detection

### Disabling Expansion

Disable variable expansion if needed:

```python
config = load_env(expand_vars=False)
# ${VAR} syntax is treated as literal text
```

## List Parsing

Two formats are supported for lists:

### JSON Arrays

```bash
# .env
DOMAINS=["a.com","b.com","c.com"]
NUMBERS=[1,2,3,4,5]
```

```python
config = load_env(types={"DOMAINS": list, "NUMBERS": list})
print(config["DOMAINS"])   # ["a.com", "b.com", "c.com"]
print(config["NUMBERS"])   # ["1", "2", "3", "4", "5"] (still strings)
```

!!! note "JSON List Parsing"
    - Must start with `[` and end with `]`
    - Valid JSON syntax required
    - Falls back to comma-separated if JSON parsing fails

### Comma-Separated

```bash
# .env
LIMITS=10,20,400
HOSTS=192.168.1.1,10.0.0.1,172.16.0.1
```

```python
config = load_env(types={"LIMITS": list, "HOSTS": list})
print(config["LIMITS"])  # ["10", "20", "400"]
print(config["HOSTS"])   # ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
```

!!! tip "List Type Handling"
    - JSON arrays are parsed as-is (preserves types if valid JSON)
    - Comma-separated values are always strings
    - Empty lists: `[]` or empty string `""` both result in `[]`

## Validation Rules

Add custom validation logic:

```python
config = load_env(
    types={"PORT": int},
    rules={
        "PORT": lambda v: 1024 < v < 65535,
        "TIMEOUT": lambda v: v > 0,
        "ALLOWED_HOSTS": lambda hosts: len(hosts) > 0
    }
)
# Raises ValidationError if any rule fails
```

### Rule Function Signature

Validation rules receive the **typed value** (after casting):

```python
rules = {
    "PORT": lambda v: isinstance(v, int) and 1024 < v < 65535,
    "EMAIL": lambda v: "@" in v and "." in v.split("@")[1],
    "HOSTS": lambda hosts: isinstance(hosts, list) and len(hosts) > 0
}
```

!!! warning "Rule Execution Order"
    Rules are executed **after** type casting. If type casting fails, rules are not executed.

## Strict Mode

Enable strict mode to catch unknown variables:

```python
config = load_env(
    required=["API_KEY"],
    types={"PORT": int},
    strict=True
)
# Warns about variables in .env not in required/types/defaults
```

!!! note "Strict Mode Behavior"
    - Warns (does not fail) about unknown variables
    - Useful for catching typos in variable names
    - Recommended for production environments

## Safe Representation

Get a safe representation with masked secrets:

```python
config = load_env()

# Safe for logging (secrets masked)
safe = config.safe_repr()
print(safe)
# {
#   "API_KEY": "****1234",
#   "PORT": 8080,
#   "DB_PASSWORD": "****"
# }

# Full access (use with caution)
value = config["API_KEY"]  # Full value, not masked
```

!!! danger "Never Log Full Config"
    Always use `safe_repr()` for logging:
    ```python
    # ❌ BAD
    logging.info(f"Config: {config}")
    
    # ✅ GOOD
    logging.info(f"Config: {config.safe_repr()}")
    ```

## Export Configuration

Export configuration to files:

```python
config = load_env()

# Export to JSON (secrets masked by default)
config.save("config.json", format="json")

# Export to YAML
config.save("config.yaml", format="yaml")

# Export with unmasked values (dangerous!)
config.save("config.json", format="json", safe=False)
```

!!! warning "Export Safety"
    By default, `save()` uses `safe_repr()` which masks secrets. Only use `safe=False` if you're certain the output is secure.

## Common Patterns

### Development vs Production

```python
import os

env = os.getenv("ENVIRONMENT", "dev")
config = load_env(
    env=env,
    required=["API_KEY"] if env == "prod" else [],
    strict=env == "prod"
)
```

### Configuration with Fallbacks

```python
config = load_env(
    defaults={
        "PORT": 8080,
        "DEBUG": False
    },
    types={
        "PORT": int,
        "DEBUG": bool
    }
)
# Uses defaults if not set, but still validates types
```

### Required Variables with Types

```python
config = load_env(
    required=["API_KEY", "DB_URI"],
    types={
        "PORT": int,
        "TIMEOUT": float,
        "DEBUG": bool
    }
)
# Ensures API_KEY and DB_URI exist
# Casts PORT, TIMEOUT, DEBUG to their types
```

## Next Steps

- Learn about [Type Casting](../core-concepts/type-casting.md) - Detailed type casting rules
- Explore [Validation](../core-concepts/validation.md) - Advanced validation
- Set up [Schema Support](../core-concepts/schema.md) - Type-safe schemas
