# env-loader-pro Enterprise Architecture

## 🏗️ Architecture Overview

Modular, enterprise-grade architecture with clear separation of concerns and full observability.

### Directory Structure

```
env_loader_pro/
├── core/                    # Core functionality
│   ├── loader.py           # Unified load_env API
│   ├── merger.py           # Source priority resolution
│   ├── schema.py           # Enhanced schema validation
│   ├── tracing.py          # Origin tracking & observability
│   ├── cache.py            # TTL-based caching
│   ├── audit.py            # Audit trail system
│   ├── policy.py           # Failure policy control
│   ├── policy_code.py      # Policy-as-code enforcement
│   ├── diff.py             # Configuration drift detection
│   └── performance.py      # Performance monitoring
│
├── providers/              # Configuration source providers
│   ├── base.py             # Abstract provider interface
│   ├── azure.py            # Azure Key Vault
│   ├── aws.py              # AWS Secrets Manager & SSM
│   ├── docker.py           # Docker/K8s secrets
│   └── filesystem.py       # Filesystem-mounted configs
│
├── crypto/                 # Encryption support
│   ├── decryptor.py        # Generic decrypt interface
│   ├── age.py              # age encryption
│   ├── gpg.py              # GPG encryption
│   └── lifecycle.py        # Encrypted file lifecycle
│
├── watch/                  # Live reloading
│   └── reloader.py         # File watching & reload
│
├── exporters/              # Configuration exporters
│   ├── env_example.py      # Generate .env.example
│   ├── kubernetes.py       # K8s ConfigMap/Secret YAML
│   └── terraform.py        # Terraform .tfvars
│
└── utils/                  # Utility modules
    ├── masking.py          # Secret masking
    ├── autodetect.py       # Runtime environment detection
    └── logging.py           # Structured logging
```

## 🎯 Core Principles

### 1. Security First
- Automatic secret masking in logs and safe_repr()
- No secrets in plaintext unless explicitly requested
- Cloud providers override local config by default (secrets win)
- Full audit trail for compliance

### 2. Cloud-Agnostic Core
- Azure and AWS integrations are optional plugins
- Core library works without cloud SDKs
- Graceful degradation if providers unavailable

### 3. Deterministic Configuration Precedence

**Priority Order (highest to lowest):**
1. **Cloud providers** (Azure Key Vault, AWS Secrets Manager)
2. **System environment variables**
3. **Docker/K8s mounted secrets**
4. **.env.{env}** (environment-specific)
5. **Base .env file**
6. **Schema defaults**

This order is **fixed and documented** - no ambiguity.

### 4. Enterprise Defaults
- Validation enabled by default
- Tracing available for observability
- Caching enabled for performance
- Strict mode available for production

## 📦 Unified API

### Basic Usage

```python
from env_loader_pro import load_env

config = load_env(
    env="prod",
    strict=True,
    trace=True,
    providers=[...],
    cache=True,
    cache_ttl=3600,
)
```

### With Audit Trail

```python
config, audit = load_env(audit=True)

# Get provenance for a variable
entry = audit.get("API_KEY")
print(f"Source: {entry.source}, Provider: {entry.provider}")

# Export audit as JSON
print(audit.to_json())
```

### With Failure Policies

```python
config = load_env(
    providers=[azure_provider, aws_provider],
    failure_policy={
        "azure": "fail",      # Raise error on Azure failure
        "aws": "fallback",    # Silently continue if AWS fails
        "filesystem": "warn"  # Log warning but continue
    }
)
```

### With Policy-as-Code

```python
# policy.yaml:
# require:
#   - API_KEY
#   - DB_PASSWORD
# forbid:
#   - DEBUG
# sources:
#   API_KEY: azure

config = load_env(
    env="prod",
    policy="policy.yaml"  # Enforces requirements
)
```

## 🔍 Observability & Tracing

### Origin Tracking

```python
config = load_env(trace=True)

# Get origin of a variable
origin = config.trace("API_KEY")  # Returns: "azure", "aws", "system", etc.

# Get all origins
origins = config.get_origins()
# Returns: {"API_KEY": "azure", "PORT": "file", ...}
```

### Audit Trail

```python
config, audit = load_env(audit=True)

# Summary statistics
summary = audit.get_summary()
# {
#   "total_variables": 10,
#   "masked_variables": 3,
#   "sources": {"azure": 2, "file": 8},
#   "providers": {"AzureKeyVaultProvider": 2}
# }

# Export for compliance
audit.to_json()
```

## 🔐 Security Features

### Automatic Secret Masking

```python
config = load_env()

# Safe representation (secrets masked)
safe = config.safe_repr()
# {"API_KEY": "****1234", "PORT": 8080}

# Full access (secrets visible)
value = config["API_KEY"]  # Full value
```

### Encrypted .env Files

```python
# Encrypt
envloader encrypt .env --method age

# Load encrypted
config = load_env(
    path=".env.enc",
    encrypted=True,
    encryption_key="/path/to/key"
)
```

## 🔄 Configuration Lifecycle

### Load Flow

```
1. Load from providers (Azure, AWS) → highest priority
2. Merge system environment variables
3. Merge Docker/K8s mounted secrets
4. Load .env.{env} (environment-specific)
5. Load base .env file
6. Apply schema defaults → lowest priority
7. Type casting
8. Validation (required, rules, policy)
9. Return ConfigDict with metadata
```

### Audit Flow

```
For each variable:
1. Record source (azure, aws, system, file, etc.)
2. Record provider name (if applicable)
3. Mark as masked if secret pattern matches
4. Record timestamp
5. Store in audit trail
```

### Failure Policy Flow

```
For each provider:
1. Attempt to load
2. On error:
   - If policy = "fail" → raise ProviderError
   - If policy = "warn" → log warning, continue
   - If policy = "fallback" → silently continue
3. Merge results
```

## 🔌 Provider System

### Provider Interface

```python
from env_loader_pro.providers import BaseProvider

class CustomProvider(BaseProvider):
    def get(self, key: str) -> Optional[str]:
        """Get single value."""
        pass
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        pass
    
    def get_all(self) -> Dict[str, str]:
        """Get all values (optional, for efficiency)."""
        pass
    
    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get secret metadata (TTL, rotation, etc.)."""
        pass
```

### Provider Capabilities

```python
provider = AzureKeyVaultProvider(...)
capabilities = provider.capabilities

# {
#   "batch": True,        # Supports get_many
#   "cacheable": True,    # Values can be cached
#   "rotatable": False,   # Supports secret rotation
#   "watchable": False,   # Supports watching for changes
#   "metadata": True      # Provides secret metadata
# }
```

## 📊 Performance & Monitoring

### Performance SLAs

- **Cold start**: < 500ms
- **Warm load**: < 50ms
- **Cached**: < 5ms

### Circuit Breaker

```python
from env_loader_pro.core import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)

if breaker.should_attempt():
    try:
        value = provider.get("KEY")
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
```

## 🧪 Testing Strategy

### Unit Tests
- Core functionality (loading, merging, validation)
- Provider mocking
- Audit trail correctness
- Failure policy enforcement
- Policy-as-code validation

### Integration Tests
- End-to-end configuration loading
- Provider integration (with mocks)
- CLI command execution
- CI-safe mode verification

## 📝 Best Practices

1. **Use strict mode in production** to catch configuration errors early
2. **Enable tracing** for debugging and observability
3. **Use cloud providers** for secrets in production
4. **Cache provider values** to reduce API calls
5. **Use schema validation** for type safety
6. **Enable audit trail** for compliance
7. **Set failure policies** per environment
8. **Use policy-as-code** for governance

## 🔄 Migration from python-dotenv

The API is designed to be a drop-in replacement with enhanced features:

```python
# Before (python-dotenv)
from dotenv import load_dotenv
load_dotenv()
port = int(os.getenv("PORT", "8080"))

# After (env-loader-pro)
from env_loader_pro import load_env
config = load_env(types={"PORT": int}, defaults={"PORT": 8080})
port = config["PORT"]  # Already an int
```
