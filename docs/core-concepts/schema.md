# Schema Support

Use Pydantic models or Python dataclasses for type-safe configuration with automatic validation. Schemas provide better type safety, IDE autocomplete, and comprehensive validation compared to the basic `types` parameter.

## Why Use Schemas?

### Problem with Basic Types

```python
# Basic approach
config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "DEBUG": bool},
    defaults={"PORT": 8080}
)

# Issues:
# - No IDE autocomplete
# - No type checking
# - Validation logic scattered
# - Hard to document structure
```

### Solution: Schemas

```python
# Schema approach
class Config(BaseModel):
    port: int = 8080
    debug: bool = False
    api_key: str  # Required

config = load_with_schema(Config)
# - Full IDE autocomplete
# - Type checking
# - Centralized validation
# - Self-documenting
```

## Pydantic Models

### Basic Example

```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

class Config(BaseModel):
    port: int
    debug: bool
    api_key: str

config = load_with_schema(Config)
print(config.port)    # Typed access with autocomplete
print(config.debug)   # bool
print(config.api_key) # str
```

### With Defaults

```python
class Config(BaseModel):
    port: int = 8080
    debug: bool = False
    api_key: str  # Required (no default)

config = load_with_schema(Config)
# port defaults to 8080 if not set
# debug defaults to False if not set
# api_key is required (raises error if missing)
```

### With Validators

Pydantic validators provide powerful validation:

```python
from pydantic import BaseModel, validator

class Config(BaseModel):
    port: int = 8080
    email: str
    timeout: int = 30
    
    @validator('port')
    def validate_port(cls, v):
        if not 1024 < v < 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v

config = load_with_schema(Config)
# All validators run automatically
```

### Field Validation

Use Pydantic's `Field` for more control:

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    port: int = Field(default=8080, ge=1024, le=65535)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    timeout: int = Field(default=30, gt=0)

config = load_with_schema(Config)
# Field validators run automatically
```

### Complex Types

```python
from typing import List, Optional, Dict
from pydantic import BaseModel

class Config(BaseModel):
    port: int = 8080
    hosts: List[str]  # List of strings
    metadata: Optional[Dict[str, str]] = None  # Optional dict
    tags: List[str] = []  # List with default

config = load_with_schema(Config)
```

## Dataclasses

### Basic Example

```python
from env_loader_pro import load_with_schema
from dataclasses import dataclass

@dataclass
class Config:
    port: int
    debug: bool
    api_key: str

config = load_with_schema(Config)
print(config.port)  # Typed access
```

### With Defaults

```python
@dataclass
class Config:
    port: int = 8080
    debug: bool = False
    api_key: str = ""  # Optional with default

config = load_with_schema(Config)
```

### Dataclass vs Pydantic

| Feature | Dataclass | Pydantic |
|---------|-----------|----------|
| Type safety | ✅ | ✅ |
| Validation | ❌ (manual) | ✅ (automatic) |
| IDE autocomplete | ✅ | ✅ |
| Default values | ✅ | ✅ |
| Field validation | ❌ | ✅ |
| JSON serialization | ❌ | ✅ |

!!! tip "When to Use Each"
    - **Pydantic**: When you need validation, JSON serialization, or complex types
    - **Dataclass**: When you want simple type safety without extra dependencies

## Case-Insensitive Matching

Environment variables are typically `UPPERCASE`, but schema fields can be `lowercase`:

```bash
# .env
API_KEY=secret123
PORT=8080
DEBUG=true
```

```python
class Config(BaseModel):
    api_key: str  # lowercase
    port: int     # lowercase
    debug: bool   # lowercase

config = load_with_schema(Config)
# Automatically matches UPPERCASE env vars
# config.api_key = "secret123"
# config.port = 8080
# config.debug = True
```

!!! note "Matching Rules"
    - Case-insensitive matching
    - `API_KEY` matches `api_key`
    - `PORT` matches `port`
    - Underscores are preserved

## Environment-Specific Loading

```python
config = load_with_schema(Config, env="prod")
# Loads from .env.prod
```

## Advanced Features

### Optional Fields

```python
from typing import Optional

class Config(BaseModel):
    port: int = 8080
    api_key: str
    optional_field: Optional[str] = None
    another_optional: Optional[int] = None

config = load_with_schema(Config)
# optional_field is None if not set
# another_optional is None if not set
```

### Nested Models

```python
class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    ssl: bool = True

class Config(BaseModel):
    database: DatabaseConfig
    api_key: str

# Use nested keys in .env:
# DATABASE__HOST=localhost
# DATABASE__PORT=5432
# DATABASE__SSL=true
```

```python
config = load_with_schema(Config)
print(config.database.host)  # "localhost"
print(config.database.port)  # 5432
print(config.database.ssl)   # True
```

### Union Types

```python
from typing import Union

class Config(BaseModel):
    log_level: Union[str, int]  # Can be string or int
    # .env: LOG_LEVEL=info (string)
    # or: LOG_LEVEL=10 (int)
```

### Enum Types

```python
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class Config(BaseModel):
    log_level: LogLevel = LogLevel.INFO

config = load_with_schema(Config)
# log_level is validated against enum values
```

## Schema with Providers

Schemas work with cloud providers:

```python
from env_loader_pro import load_with_schema
from env_loader_pro.providers import AzureKeyVaultProvider

class Config(BaseModel):
    api_key: str
    db_password: str
    port: int = 8080

provider = AzureKeyVaultProvider(vault_url="https://myvault.vault.azure.net")
config = load_with_schema(Config, providers=[provider])

# api_key and db_password from Azure
# port from default or .env
```

## Schema with Audit

```python
config, audit = load_with_schema(Config, audit=True)

# Get audit for schema fields
entry = audit.get("api_key")
print(f"api_key came from: {entry.source}")
```

## Error Handling

### Missing Required Fields

```python
class Config(BaseModel):
    api_key: str  # Required

# .env: (api_key missing)
config = load_with_schema(Config)
# Raises: ValidationError: api_key field required
```

### Invalid Types

```python
class Config(BaseModel):
    port: int

# .env: PORT=not-a-number
config = load_with_schema(Config)
# Raises: ValidationError: port must be an integer
```

### Validation Errors

```python
class Config(BaseModel):
    port: int = 8080
    
    @validator('port')
    def validate_port(cls, v):
        if not 1024 < v < 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v

# .env: PORT=80
config = load_with_schema(Config)
# Raises: ValidationError: Port must be between 1024 and 65535
```

## Best Practices

### 1. Use Pydantic for Complex Validation

```python
# ✅ GOOD: Centralized validation
class Config(BaseModel):
    port: int = Field(ge=1024, le=65535)
    email: str = Field(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')

# ❌ BAD: Validation scattered
config = load_env(
    types={"PORT": int},
    rules={"PORT": lambda v: 1024 < v < 65535}
)
```

### 2. Document with Docstrings

```python
class Config(BaseModel):
    """Application configuration.
    
    Attributes:
        port: Server port (1024-65535)
        api_key: API key for external service
        debug: Enable debug mode
    """
    port: int = 8080
    api_key: str
    debug: bool = False
```

### 3. Use Defaults for Optional Values

```python
# ✅ GOOD: Clear defaults
class Config(BaseModel):
    port: int = 8080
    timeout: int = 30

# ❌ BAD: No defaults, unclear if optional
class Config(BaseModel):
    port: int
    timeout: int
```

### 4. Validate Early

```python
# Application startup
try:
    config = load_with_schema(Config, env="prod")
except ValidationError as e:
    logger.error(f"Invalid configuration: {e}")
    sys.exit(1)
```

## Comparison

### Without Schema

```python
config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "DEBUG": bool},
    defaults={"PORT": 8080, "DEBUG": False}
)
port = config["PORT"]  # Dict access, no autocomplete
```

### With Schema

```python
config = load_with_schema(Config)
port = config.port  # Typed access with autocomplete
```

## Related Topics

- [Type Casting](../core-concepts/type-casting.md) - Automatic type conversion
- [Validation](../core-concepts/validation.md) - Validation rules
