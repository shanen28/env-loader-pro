# Type Casting

env-loader-pro automatically casts environment variable strings to their specified types. This page documents the exact casting rules, edge cases, and behavior.

## Overview

Environment variables are always strings. Type casting converts these strings to the appropriate Python types based on the `types` parameter.

```python
config = load_env(types={"PORT": int})
port = config["PORT"]  # int, not string
```

## Supported Types

### Integer (`int`)

Casts string to integer using Python's `int()` constructor:

```python
config = load_env(types={"PORT": int})

# Valid inputs
PORT=8080        # → 8080 (int)
PORT=0           # → 0 (int)
PORT=-100        # → -100 (int)

# Invalid inputs raise EnvLoaderError
PORT=not-a-number  # → EnvLoaderError
PORT=12.5         # → EnvLoaderError (use float instead)
```

!!! note "Integer Parsing"
    - Leading/trailing whitespace is stripped
    - Uses Python's `int()` constructor
    - Hexadecimal (`0xFF`) and octal (`0o77`) formats are supported
    - Scientific notation (`1e3`) is **not** supported (use float)

### Boolean (`bool`)

Boolean casting supports multiple formats for flexibility:

```python
config = load_env(types={"DEBUG": bool})

# True values (case-insensitive)
DEBUG=true   # → True
DEBUG=1      # → True
DEBUG=yes    # → True
DEBUG=y      # → True
DEBUG=t      # → True

# False values (case-insensitive)
DEBUG=false  # → False
DEBUG=0      # → False
DEBUG=no     # → False
DEBUG=n      # → False
DEBUG=f      # → False

# Invalid values raise EnvLoaderError
DEBUG=maybe  # → EnvLoaderError: Cannot cast 'maybe' to bool
```

!!! tip "Boolean Best Practices"
    - Use `true`/`false` for clarity
    - Use `1`/`0` for brevity
    - Avoid ambiguous values like `yes`/`no` in production

### Float (`float`)

Casts string to float using Python's `float()` constructor:

```python
config = load_env(types={"RATE": float})

# Valid inputs
RATE=3.14        # → 3.14 (float)
RATE=0.5         # → 0.5 (float)
RATE=100         # → 100.0 (float)
RATE=1e-3        # → 0.001 (float, scientific notation)

# Invalid inputs raise EnvLoaderError
RATE=not-a-float # → EnvLoaderError
```

!!! note "Float Precision"
    - Uses Python's `float()` constructor
    - Scientific notation is supported (`1e3`, `1.5e-2`)
    - Infinity and NaN are supported (`inf`, `nan`)

### List (`list`)

List casting supports two formats: JSON arrays and comma-separated values.

#### JSON Arrays

JSON arrays are parsed first if the value starts with `[` and ends with `]`:

```bash
# .env
DOMAINS=["a.com","b.com","c.com"]
NUMBERS=[1,2,3]
MIXED=["a",1,true,null]
```

```python
config = load_env(types={"DOMAINS": list, "NUMBERS": list, "MIXED": list})

print(config["DOMAINS"])  # ["a.com", "b.com", "c.com"]
print(config["NUMBERS"])  # [1, 2, 3] (preserves JSON types)
print(config["MIXED"])    # ["a", 1, True, None] (preserves JSON types)
```

!!! warning "JSON Parsing"
    - Must be valid JSON syntax
    - If JSON parsing fails, falls back to comma-separated
    - JSON types are preserved (numbers, booleans, null)

#### Comma-Separated Values

If JSON parsing fails or value doesn't start with `[`, comma-separated parsing is used:

```bash
# .env
LIMITS=10,20,400
HOSTS=192.168.1.1,10.0.0.1,172.16.0.1
EMPTY=
```

```python
config = load_env(types={"LIMITS": list, "HOSTS": list, "EMPTY": list})

print(config["LIMITS"])  # ["10", "20", "400"] (strings)
print(config["HOSTS"])   # ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
print(config["EMPTY"])   # [] (empty list)
```

!!! note "Comma-Separated Behavior"
    - Values are always strings (not parsed as numbers)
    - Empty values are filtered out
    - Leading/trailing whitespace is stripped from each item

#### Empty Lists

```bash
# .env
EMPTY_JSON=[]
EMPTY_CSV=
EMPTY_SPACE= 
```

```python
config = load_env(types={"EMPTY_JSON": list, "EMPTY_CSV": list, "EMPTY_SPACE": list})

print(config["EMPTY_JSON"])   # [] (empty list)
print(config["EMPTY_CSV"])    # [] (empty list)
print(config["EMPTY_SPACE"]) # [] (empty list)
```

### String (Default)

If no type is specified, values remain strings:

```python
config = load_env()
# All values are strings, no casting applied
```

## Type Casting Examples

### Complete Example

```bash
# .env
PORT=8080
DEBUG=true
TIMEOUT=30.5
DOMAINS=["api.example.com","web.example.com"]
ALLOWED_IPS=192.168.1.1,10.0.0.1
RATE=0.05
```

```python
config = load_env(
    types={
        "PORT": int,
        "DEBUG": bool,
        "TIMEOUT": float,
        "DOMAINS": list,
        "ALLOWED_IPS": list,
        "RATE": float
    }
)

print(type(config["PORT"]))        # <class 'int'>
print(type(config["DEBUG"]))       # <class 'bool'>
print(type(config["TIMEOUT"]))     # <class 'float'>
print(type(config["DOMAINS"]))     # <class 'list'>
print(type(config["ALLOWED_IPS"])) # <class 'list'>
print(type(config["RATE"]))        # <class 'float'>
```

## Error Handling

### Invalid Type Conversion

When a value cannot be cast to the specified type, `EnvLoaderError` is raised:

```python
# .env: PORT=not-a-number
config = load_env(types={"PORT": int})
# Raises: EnvLoaderError: Failed to cast env value 'not-a-number' to int
```

### Invalid Boolean

Boolean casting is strict - only specific values are accepted:

```python
# .env: DEBUG=maybe
config = load_env(types={"DEBUG": bool})
# Raises: EnvLoaderError: Cannot cast 'maybe' to bool
```

### Invalid List Format

If a list value cannot be parsed:

```python
# .env: DOMAINS=[invalid json
config = load_env(types={"DOMAINS": list})
# Falls back to comma-separated: ["[invalid", "json"]
```

## Type Casting Order

Type casting happens **after** all sources are merged:

1. Load from all sources (providers, system, files)
2. Merge with precedence
3. Expand variables (`${VAR}`)
4. **Apply type casting** ← Here
5. Apply defaults (if not already cast)
6. Validate

!!! note "Casting After Merging"
    This means type casting sees the **final merged value**, not individual source values.

## Edge Cases

### Whitespace Handling

All values are stripped of leading/trailing whitespace before casting:

```bash
# .env
PORT=  8080  
DEBUG=  true  
```

```python
config = load_env(types={"PORT": int, "DEBUG": bool})
print(config["PORT"])   # 8080 (whitespace stripped)
print(config["DEBUG"])  # True (whitespace stripped)
```

### Empty Values

Empty values behave differently by type:

```bash
# .env
EMPTY_STR=
EMPTY_INT=
EMPTY_BOOL=
EMPTY_LIST=
```

```python
config = load_env(
    types={"EMPTY_STR": str, "EMPTY_INT": int, "EMPTY_BOOL": bool, "EMPTY_LIST": list},
    defaults={"EMPTY_STR": "", "EMPTY_INT": 0, "EMPTY_BOOL": False, "EMPTY_LIST": []}
)

# Empty string: remains empty string
# Empty int: raises EnvLoaderError (use default instead)
# Empty bool: raises EnvLoaderError (use default instead)
# Empty list: becomes [] (empty list)
```

### None Values

JSON `null` values are preserved in JSON arrays:

```bash
# .env
VALUES=[1, null, "test"]
```

```python
config = load_env(types={"VALUES": list})
print(config["VALUES"])  # [1, None, "test"]
```

## Type Safety with Schemas

For better type safety and validation, use schema validation:

```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

class Config(BaseModel):
    port: int
    debug: bool
    timeout: float
    domains: list[str]

config = load_with_schema(Config)
# All types validated and enforced by Pydantic
```

!!! tip "Schema vs Types"
    - `types` parameter: Simple casting, no validation
    - Schema (Pydantic/dataclass): Type validation + business rules

## Best Practices

1. **Always specify types** for non-string values
   ```python
   # ❌ BAD
   port = int(config["PORT"])
   
   # ✅ GOOD
   config = load_env(types={"PORT": int})
   port = config["PORT"]
   ```

2. **Use schemas** for complex configurations
   ```python
   # Better type safety and validation
   config = load_with_schema(Config)
   ```

3. **Handle casting errors** gracefully
   ```python
   try:
       config = load_env(types={"PORT": int})
   except EnvLoaderError as e:
       # Handle invalid type
       pass
   ```

4. **Use defaults** for optional typed values
   ```python
   config = load_env(
       types={"PORT": int},
       defaults={"PORT": 8080}
   )
   ```

## Related Topics

- [Validation](../core-concepts/validation.md) - Validate values after casting
- [Schema Support](../core-concepts/schema.md) - Type-safe schemas with validation
