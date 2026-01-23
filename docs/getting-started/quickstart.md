# Quick Start

Get started with env-loader-pro in 5 minutes.

## Basic Example

```python
from env_loader_pro import load_env

# Load configuration
config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "DEBUG": bool},
    defaults={"PORT": 8080}
)

# Use configuration
print(config["PORT"])   # 8080 (int)
print(config["DEBUG"])  # True (bool)
print(config["API_KEY"]) # Your API key
```

## Create .env File

Create a `.env` file in your project root:

```bash
# .env
PORT=8080
DEBUG=true
API_KEY=your-secret-key-here
```

## Load and Use

```python
from env_loader_pro import load_env

config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "DEBUG": bool}
)

# Access values
port = config["PORT"]      # Already an int!
debug = config["DEBUG"]    # Already a bool!
api_key = config["API_KEY"] # String
```

## With Cloud Secrets (Azure)

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AzureKeyVaultProvider

# Create provider
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net"
)

# Load with provider
config = load_env(
    env="prod",
    providers=[provider]
)

# Secrets from Azure Key Vault override local .env
print(config["DB_PASSWORD"])  # From Azure
```

## With Cloud Secrets (AWS)

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AWSSecretsManagerProvider

# Create provider
provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod",
    region="us-east-1"
)

# Load with provider
config = load_env(
    env="prod",
    providers=[provider]
)
```

## With Schema Validation

```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

# Define schema
class Config(BaseModel):
    port: int = 8080
    debug: bool = False
    api_key: str  # Required

# Load and validate
config = load_with_schema(Config, env="prod")

# Typed access
print(config.port)    # int
print(config.debug)   # bool
print(config.api_key) # str
```

## CLI Usage

```bash
# Show configuration
envloader show

# Validate
envloader validate --required API_KEY PORT

# Export to JSON
envloader export --output config.json
```

## Next Steps

- Learn about [Configuration Precedence](../core-concepts/precedence.md)
- Explore [Type Casting](../core-concepts/type-casting.md)
- Set up [Cloud Providers](../providers/overview.md)
- Enable [Audit Trail](../enterprise/audit.md)
