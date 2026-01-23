# Architecture Overview

High-level architecture and design principles.

## Directory Structure

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
│   ├── policy_code.py     # Policy-as-code enforcement
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

## Core Principles

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
1. Cloud providers (Azure Key Vault, AWS Secrets Manager)
2. System environment variables
3. Docker/K8s mounted secrets
4. .env.{env} (environment-specific)
5. Base .env file
6. Schema defaults

### 4. Enterprise Defaults
- Validation enabled by default
- Tracing available for observability
- Caching enabled for performance
- Strict mode available for production

## Load Flow

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

## Related Topics

- [Design Principles](../architecture/principles.md)
- [Provider System](../architecture/providers.md)
