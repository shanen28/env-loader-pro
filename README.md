# env-loader-pro

**Enterprise-grade typed, validated, and secure environment variable loader** for Python with automatic type casting, validation, secret masking, cloud secrets integration, and full observability.

## 🎯 What Problem Does This Solve?

Traditional `.env` loaders are basic and unsafe. **env-loader-pro** provides:

- **Type safety** - Automatic casting to int, bool, list, etc.
- **Cloud secrets** - Azure Key Vault, AWS Secrets Manager integration
- **Audit trail** - Complete provenance tracking for compliance
- **Policy enforcement** - Policy-as-code for configuration governance
- **CI/CD safe** - All commands work without cloud credentials
- **Secret security** - Automatic masking, never logs secrets

## 🚀 Key Features

- ✅ **Load from `.env` + system env** with deterministic precedence
- ✅ **Automatic type casting** (int, bool, list, JSON)
- ✅ **Required/optional validation** with helpful errors
- ✅ **Default values** support
- ✅ **Secret masking** for safe printing/logging
- ✅ **Environment variable expansion** (`${VAR}` syntax)
- ✅ **Multiple environment support** (`.env.dev`, `.env.prod`, etc.)
- ✅ **Cloud secrets** - Azure Key Vault, AWS Secrets Manager
- ✅ **Audit trail** - Full provenance tracking
- ✅ **Failure policies** - Per-provider error handling
- ✅ **Policy-as-code** - JSON/YAML policy enforcement
- ✅ **Configuration diff** - Drift detection
- ✅ **Schema support** (Pydantic models & dataclasses)
- ✅ **CLI tool** for common operations
- ✅ **CI/CD safe** - No cloud access required

## 📦 Installation

```bash
pip install env-loader-pro
```

### Optional Dependencies

```bash
# For Pydantic schema support
pip install env-loader-pro[pydantic]

# For Azure Key Vault
pip install env-loader-pro[azure]

# For AWS Secrets Manager
pip install env-loader-pro[aws]

# For YAML export
pip install env-loader-pro[yaml]

# For everything
pip install env-loader-pro[all]
```

## 🎯 Quickstart

### Basic Usage

```python
from env_loader_pro import load_env

config = load_env(
    required=["API_KEY"],
    types={"PORT": int, "DEBUG": bool},
    defaults={"PORT": 8080}
)

print(config["PORT"])  # 8080 (int)
print(config["DEBUG"])  # True (bool)
```

### With Cloud Secrets (Azure)

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AzureKeyVaultProvider

provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net"
)

config = load_env(
    env="prod",
    providers=[provider],
    audit=True  # Track provenance
)

# Get audit trail
config, audit = load_env(audit=True)
print(audit.to_json())
```

### With Cloud Secrets (AWS)

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AWSSecretsManagerProvider

provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod",
    region="us-east-1"
)

config = load_env(
    env="prod",
    providers=[provider],
    failure_policy={"aws": "fallback"}  # Graceful degradation
)
```

### With Policy-as-Code

```python
from env_loader_pro import load_env

# policy.yaml:
# require:
#   - API_KEY
#   - DB_PASSWORD
# forbid:
#   - DEBUG

config = load_env(
    env="prod",
    policy="policy.yaml"  # Enforces requirements
)
```

### Schema Support

```python
from env_loader_pro import load_with_schema
from pydantic import BaseModel

class Config(BaseModel):
    port: int = 8080
    debug: bool = False
    api_key: str  # Required

config = load_with_schema(Config, env="prod")
print(config.port)  # Typed access
```

## 🛠️ CLI Tool

```bash
# Show environment variables
envloader show --env prod

# Validate (CI-safe, no cloud access)
envloader validate --ci --required API_KEY PORT

# Audit trail
envloader audit --json

# Explain precedence
envloader explain

# Configuration diff
envloader diff --ci --deny-secret-changes

# Export to JSON/YAML
envloader export --output config.json --format json

# Generate .env.example
envloader generate-example --required API_KEY PORT
```

## 🔒 Security Features

- **Automatic secret masking** - Keys containing `secret`, `key`, `token`, `password`, `pwd` are masked
- **Audit trail** - Complete provenance tracking (source, provider, timestamp)
- **Policy enforcement** - Require/forbid variables via policy files
- **Secret change detection** - Prevent accidental exposure
- **Encrypted .env** - Support for age/GPG encrypted files
- **Never logs secrets** - All outputs are safe

## 📊 Configuration Precedence

Deterministic priority order (highest to lowest):

1. **Cloud providers** (Azure Key Vault, AWS Secrets Manager)
2. **System environment variables**
3. **Docker/K8s mounted secrets**
4. **`.env.{env}`** (environment-specific)
5. **Base `.env` file**
6. **Schema defaults**

See `envloader explain` for detailed documentation.

## 📚 Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - Technical design and internals
- **[Security Model](SECURITY.md)** - Security guarantees and secret handling
- **[Contributing](CONTRIBUTING.md)** - How to contribute

## 🧪 Testing

```bash
pip install -e ".[test]"
pytest tests/
```

## 📝 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
