# env-loader-pro Features

## 🎯 Core Features

### 1. **Automatic Type Casting**
Automatically converts environment variables to their specified types (int, bool, list, etc.) - no manual conversion needed!

```python
config = load_env(types={"PORT": int, "DEBUG": bool, "TIMEOUT": float})
# PORT is automatically an int, DEBUG is a bool, TIMEOUT is a float
```

**Supported Types:**
- `int`, `float`, `str` (default)
- `bool` (supports: true/false, 1/0, yes/no, y/n, t/f)
- `list` (supports JSON arrays and comma-separated values)

---

### 2. **Required Variable Validation**
Validates that all required environment variables are present before your app starts, preventing runtime errors.

```python
config = load_env(required=["API_KEY", "DB_URI"])
# Raises EnvLoaderError if API_KEY or DB_URI is missing
```

---

### 3. **Default Values**
Provide default values for optional configuration variables.

```python
config = load_env(
    defaults={"PORT": 8080, "DEBUG": False, "TIMEOUT": 30}
)
# If PORT is not set, it defaults to 8080
```

---

### 4. **Secret Masking**
Automatically masks sensitive values (keys containing "secret", "key", "token", "password", "pwd") when printing or logging.

```python
config = load_env()
print(config.safe_repr())
# Output: {"API_KEY": "****1234", "PORT": 8080}
```

**Security Benefit:** Prevents accidental exposure of secrets in logs or error messages.

---

### 5. **Environment Variable Expansion**
Use `${VAR}` syntax to reference other environment variables - just like shell scripts!

```python
# .env:
# BASE_URL=https://example.com
# API_ENDPOINT=${BASE_URL}/api
# FULL_URL=${API_ENDPOINT}/v1

config = load_env()
# API_ENDPOINT = "https://example.com/api"
# FULL_URL = "https://example.com/api/v1"
```

**Features:**
- Supports nested references
- Detects circular dependencies
- Works with both file and system environment variables

---

### 6. **Multiple Environment Support**
Load different configurations for dev, staging, and production environments.

```python
# File structure:
# .env          (base config)
# .env.dev      (development overrides)
# .env.prod     (production overrides)

config = load_env(env="prod")
# Loads .env.prod first, then merges with .env
# Environment-specific values override base values
```

---

### 7. **Runtime Validation Rules**
Add custom validation logic to ensure values meet your requirements.

```python
config = load_env(
    types={"PORT": int},
    rules={
        "PORT": lambda v: 1024 < v < 65535,  # Must be valid port range
        "TIMEOUT": lambda v: v > 0,          # Must be positive
    }
)
# Raises EnvLoaderError if validation fails
```

---

### 8. **Strict Mode**
Warn about unknown environment variables not defined in your schema.

```python
config = load_env(
    required=["API_KEY"],
    types={"PORT": int},
    strict=True  # Warns if .env contains variables not in schema
)
```

**Use Case:** Helps catch typos and unused variables in your `.env` file.

---

### 9. **Schema Support (Pydantic & Dataclasses)**
Use Pydantic models or Python dataclasses to define your configuration schema with automatic validation.

#### Pydantic Example:
```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

class Config(BaseModel):
    port: int
    debug: bool
    api_key: str

config = load_with_schema(Config)
print(config.port)  # Typed access with IDE autocomplete
```

#### Dataclass Example:
```python
from env_loader_pro import load_with_schema
from dataclasses import dataclass

@dataclass
class Config:
    port: int = 8080
    debug: bool = False
    api_key: str = ""

config = load_with_schema(Config)
print(config.port)  # Typed access
```

**Benefits:**
- Type safety and IDE autocomplete
- Automatic validation
- Self-documenting configuration
- Case-insensitive matching (uppercase env vars → lowercase fields)

---

### 10. **Config Export (JSON/YAML)**
Export your configuration to JSON or YAML files for sharing or deployment.

```python
config = load_env()
config.save("config.json", format="json")
config.save("config.yaml", format="yaml")
```

**Use Cases:**
- Generate config files for frontend applications
- Create configuration snapshots
- Share configuration templates

---

### 11. **Auto-generate .env.example**
Automatically generate a `.env.example` file from your schema.

```python
from env_loader_pro import generate_env_example

generate_env_example(
    required=["API_KEY", "DB_URI"],
    optional=["DEBUG", "LOG_LEVEL"],
    defaults={"PORT": 8080, "DEBUG": False},
    types={"PORT": int, "DEBUG": bool},
    output_path=".env.example"
)
```

**Output:**
```bash
# Environment Configuration
# Copy this file to .env and fill in your values

# Required variables
API_KEY=  # str
DB_URI=  # str

# Optional variables
DEBUG=False  # bool
PORT=8080  # int
```

---

### 12. **Priority System**
Control whether file or system environment variables take precedence.

```python
# File priority (default): .env overrides system env
config = load_env(priority="file")

# System priority: system env overrides .env
config = load_env(priority="system")
```

**Use Cases:**
- Docker/Kubernetes: system env overrides
- Local development: file overrides
- CI/CD: system env for secrets

---

### 13. **CLI Tool**
Command-line interface for common operations.

```bash
# Show environment variables (masked)
envloader show

# Show specific environment
envloader show --env prod

# Export to JSON
envloader export --output config.json --format json

# Validate environment
envloader validate --required API_KEY PORT

# Generate .env.example
envloader generate-example --required API_KEY PORT --optional DEBUG
```

---

## 🔄 Comparison with python-dotenv

| Feature | python-dotenv | env-loader-pro |
|---------|--------------|----------------|
| Load .env | ✅ | ✅ |
| Type casting | ❌ | ✅ |
| Required validation | ❌ | ✅ |
| Default values | ❌ | ✅ |
| Secret masking | ❌ | ✅ |
| Variable expansion | ❌ | ✅ |
| Multi-environment | ❌ | ✅ |
| Validation rules | ❌ | ✅ |
| Schema support | ❌ | ✅ |
| CLI tool | ❌ | ✅ |
| Export to JSON/YAML | ❌ | ✅ |

---

## 🎯 Use Cases

### FastAPI Applications
```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

class Settings(BaseModel):
    api_key: str
    database_url: str
    debug: bool = False
    port: int = 8000

settings = load_with_schema(Settings)
```

### Docker/Kubernetes
```python
# System environment variables override .env
config = load_env(priority="system")
```

### Development vs Production
```python
import os
env = os.getenv("ENVIRONMENT", "dev")
config = load_env(env=env)  # Loads .env.dev or .env.prod
```

### ML/AI Pipelines
```python
config = load_env(
    types={
        "BATCH_SIZE": int,
        "LEARNING_RATE": float,
        "MODEL_PATHS": list
    },
    required=["MODEL_PATH", "DATA_PATH"]
)
```

---

## 🔒 Security Features

1. **Automatic Secret Masking** - Prevents accidental log leaks
2. **Required Validation** - Ensures critical variables are set
3. **Strict Mode** - Catches configuration errors early
4. **Type Safety** - Prevents type-related security issues

---

## 📚 Additional Utilities

### Pretty Print
```python
from env_loader_pro.utils import pretty_print_config

config = load_env()
pretty_print_config(config)  # Formatted output
```

### Safe Representation
```python
config = load_env()
safe = config.safe_repr()  # All secrets masked
logger.info(f"Config: {safe}")  # Safe to log
```

---

## 🚀 Getting Started

1. **Install:**
   ```bash
   pip install env-loader-pro
   ```

2. **Create `.env` file:**
   ```bash
   PORT=8080
   DEBUG=true
   API_KEY=your-secret-key
   ```

3. **Use in your code:**
   ```python
   from env_loader_pro import load_env
   
   config = load_env(
       types={"PORT": int, "DEBUG": bool},
       required=["API_KEY"]
   )
   
   print(config["PORT"])  # 8080 (int)
   ```

---

## 📖 Full Documentation

See `README.md` for complete documentation and examples.

