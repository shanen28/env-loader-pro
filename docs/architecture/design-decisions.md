# Design Decisions

This document explains the **why** behind env-loader-pro's architecture. Each decision was made with specific tradeoffs in mind, informed by real-world production experience.

## Why Deterministic Precedence Matters

### Problem

Configuration can come from multiple sources: `.env` files, system environment, cloud vaults, Docker secrets. Without a clear precedence order, you get:

- **Non-deterministic behavior**: Same code, different results
- **Debugging nightmares**: "Why is this value wrong in production?"
- **Security risks**: Local secrets overriding production secrets
- **Compliance failures**: Can't prove where values came from

### Decision

**Fixed precedence order (highest to lowest):**

1. Cloud providers (Azure, AWS)
2. System environment variables
3. Docker/K8s mounted secrets
4. `.env.{env}` (environment-specific)
5. Base `.env` file
6. Schema defaults

This order is **documented, tested, and cannot be changed**.

### Outcome

- **Predictable**: Same precedence everywhere, every time
- **Secure by default**: Cloud secrets always win (secrets win)
- **Debuggable**: `envloader explain` shows exact order
- **Auditable**: Audit trail records which source won

### Tradeoffs

**Pros:**
- No ambiguity - developers know exactly what will happen
- Security-first - production secrets can't be overridden by local files
- Testable - precedence is deterministic

**Cons:**
- Less flexible - can't customize precedence per environment
- Learning curve - developers must understand the order
- Migration - existing code might rely on different precedence

**Why we chose this:**
In production, **predictability and security** outweigh flexibility. A developer should never accidentally use a local `.env` value in production. The fixed order prevents this.

---

## Why Failure Policies Are Explicit

### Problem

When a cloud provider fails (network outage, auth error, rate limit), what should happen?

- **Fail fast?** - Application crashes, but you know immediately
- **Silently continue?** - Application runs, but might be misconfigured
- **Log and continue?** - Application runs, but with warnings

Different environments need different behaviors. Production should fail fast. Development should be resilient.

### Decision

**Explicit per-provider failure policies:**

```python
failure_policy = {
    "azure": "fail",      # Production: fail on error
    "aws": "fallback",    # Optional: continue if unavailable
    "filesystem": "warn"  # Development: log but continue
}
```

Three policies:
- `fail` - Raise error immediately
- `warn` - Log warning and continue
- `fallback` - Silently continue

### Outcome

- **Environment-specific behavior**: Production fails fast, dev is resilient
- **Explicit intent**: Code documents what should happen on failure
- **Debuggable**: Warnings logged with context
- **Testable**: Can test failure scenarios

### Tradeoffs

**Pros:**
- Clear behavior - no guessing what happens on failure
- Flexible - different policies per provider
- Production-safe - can enforce strict policies

**Cons:**
- More configuration - must set policies explicitly
- Learning curve - developers must understand policies
- Potential for misconfiguration - wrong policy for environment

**Why we chose this:**
**Explicit is better than implicit.** In production, you want to know immediately if Azure Key Vault is down. In development, you want the app to run even if cloud providers are unavailable. Explicit policies make this clear.

---

## Why Audit Trails Are Per-Variable

### Problem

Compliance and security audits need to answer:
- "Where did this secret come from?"
- "When was it loaded?"
- "Was it from a secure source?"

Traditional logging doesn't track this. You get logs like:
```
INFO: Loaded configuration
INFO: Using DB_PASSWORD from environment
```

But you can't answer: "Was DB_PASSWORD from Azure or from a file?"

### Decision

**Per-variable audit trail** that records:
- Source (azure, aws, system, file, etc.)
- Provider name (if applicable)
- Timestamp
- Masked status
- **Never the actual value**

```python
config, audit = load_env(audit=True)
entry = audit.get("DB_PASSWORD")
# entry.source = "azure"
# entry.provider = "AzureKeyVaultProvider"
# entry.timestamp = "2024-01-15T10:30:00Z"
```

### Outcome

- **Compliance-ready**: Can prove where every value came from
- **Debuggable**: Know exactly which source provided each value
- **Secure**: Never stores actual secret values
- **Machine-readable**: JSON export for compliance systems

### Tradeoffs

**Pros:**
- Complete provenance - know source of every variable
- Compliance-friendly - audit trail for SOC 2, etc.
- Debuggable - trace configuration issues
- Safe - no secrets in audit trail

**Cons:**
- Memory overhead - stores metadata for every variable
- Performance - slight overhead to track sources
- Complexity - more code to maintain

**Why we chose this:**
**Compliance is non-negotiable.** In regulated environments, you must prove where secrets came from. Per-variable audit trails provide this proof without storing secrets.

---

## Why Cloud SDKs Are Optional

### Problem

Many configuration libraries require cloud SDKs:
- `boto3` for AWS
- `azure-identity` for Azure
- `google-cloud-secret-manager` for GCP

This creates problems:
- **Heavy dependencies**: Large SDKs slow down installation
- **Breaking changes**: SDK updates can break the library
- **CI/CD complexity**: CI pipelines need cloud credentials
- **Local development**: Can't develop without cloud access

### Decision

**Cloud SDKs are optional plugins:**

```python
# Core library works without cloud SDKs
from env_loader_pro import load_env
config = load_env()  # Works!

# Cloud providers are optional
try:
    from env_loader_pro.providers import AzureKeyVaultProvider
    provider = AzureKeyVaultProvider(...)
except ImportError:
    # Graceful degradation - use local config
    provider = None
```

### Outcome

- **Lightweight core**: Core library is small and fast
- **CI/CD friendly**: CI pipelines don't need cloud SDKs
- **Local development**: Developers can work offline
- **Graceful degradation**: App works even if providers unavailable

### Tradeoffs

**Pros:**
- Small core - fast installation, fewer dependencies
- CI/CD safe - validation works without cloud access
- Flexible - use only what you need
- Resilient - app works even if cloud unavailable

**Cons:**
- Import errors - must handle ImportError gracefully
- Feature discovery - harder to know what's available
- Documentation - must document optional features

**Why we chose this:**
**Core should work everywhere.** Not every environment has cloud access. CI pipelines, local development, air-gapped systems - all should work with the core library. Cloud providers are enhancements, not requirements.

---

## Why CI-Safe Mode Exists

### Problem

CI/CD pipelines need to validate configuration, but:
- **No cloud credentials**: CI pipelines shouldn't have production secrets
- **Deterministic behavior**: Same validation every time
- **Fast execution**: No network calls to cloud providers
- **Proper exit codes**: Pipeline should fail on validation errors

Traditional approaches:
- Skip validation in CI (bad - misses errors)
- Use cloud credentials in CI (bad - security risk)
- Mock providers (complex - requires test setup)

### Decision

**CI-safe mode** (`--ci` flag) that:
- Disables cloud providers (no network calls)
- Uses only local sources (.env files, system env)
- Provides deterministic behavior
- Returns proper exit codes

```bash
# CI pipeline
envloader validate --ci --required API_KEY PORT
# Exit code 0 = success, non-zero = failure
```

### Outcome

- **Secure**: No cloud credentials needed in CI
- **Fast**: No network calls, completes in milliseconds
- **Deterministic**: Same result every time
- **Pipeline-friendly**: Proper exit codes for automation

### Tradeoffs

**Pros:**
- Secure - no cloud credentials in CI
- Fast - no network latency
- Deterministic - same result every run
- Simple - one flag, works everywhere

**Cons:**
- Limited validation - can't validate cloud provider values
- Different behavior - CI vs production might differ
- Must remember flag - easy to forget `--ci`

**Why we chose this:**
**CI pipelines should be fast and secure.** They shouldn't need production credentials or make network calls. CI-safe mode provides validation without these requirements.

---

## Why Encrypted Configs Are Supported

### Problem

`.env` files often contain secrets. Even if you don't commit them:
- **Local storage**: Secrets stored in plaintext on disk
- **Backup exposure**: Backups might include `.env` files
- **Developer machines**: Secrets on developer laptops
- **Version control accidents**: Accidental commits

### Decision

**Support encrypted `.env` files** with multiple methods:
- `age` - Modern, simple encryption
- `GPG` - Standard, widely supported
- `openssl` - Universal, always available

```bash
# Encrypt
envloader encrypt .env --method age

# Load encrypted
config = load_env(path=".env.enc", encrypted=True)
```

**Guarantee**: Plaintext is never persisted to disk during encrypt/decrypt.

### Outcome

- **Secure storage**: Secrets encrypted at rest
- **Version control safe**: Can commit encrypted files
- **Backup safe**: Encrypted files in backups
- **Multiple methods**: Choose based on environment

### Tradeoffs

**Pros:**
- Secure - secrets encrypted at rest
- Version control friendly - can commit encrypted files
- Flexible - multiple encryption methods
- Safe - plaintext never persisted

**Cons:**
- Complexity - must manage encryption keys
- Performance - decryption overhead
- Key management - must secure encryption keys

**Why we chose this:**
**Secrets should be encrypted at rest.** Even if you don't commit `.env` files, they're stored in plaintext on disk. Encrypted configs solve this while allowing version control of encrypted files.

---

## Why Backward Compatibility Was Preserved

### Problem

env-loader-pro was refactored from a simpler library. Options:
- **Breaking changes**: Clean API, but breaks existing code
- **Backward compatible**: Supports old API, but more complex
- **Deprecation path**: Support old API, deprecate gradually

### Decision

**Full backward compatibility:**

```python
# Old API (still works)
config = load_env(
    path=".env",
    required=["API_KEY"],
    types={"PORT": int},
    defaults={"PORT": 8080},
    priority="system"
)

# New API (enhanced features)
config = load_env(
    env="prod",
    providers=[azure_provider],
    audit=True,
    failure_policy={"azure": "fail"}
)
```

All old parameters work. New features are additive.

### Outcome

- **Zero migration**: Existing code works unchanged
- **Gradual adoption**: Can adopt new features incrementally
- **Low risk**: No breaking changes in production
- **Developer friendly**: No forced rewrites

### Tradeoffs

**Pros:**
- Zero migration - existing code works
- Low risk - no breaking changes
- Gradual adoption - adopt new features when ready
- Developer friendly - no forced rewrites

**Cons:**
- API complexity - more parameters to understand
- Legacy support - must maintain old code paths
- Documentation - must document both old and new APIs

**Why we chose this:**
**Breaking changes hurt adoption.** In enterprise environments, breaking changes require migration projects, testing, and risk. Backward compatibility allows gradual adoption of new features without forcing rewrites.

---

## Why MkDocs + GitHub Pages Was Chosen

### Problem

Documentation needs:
- **Version control**: Docs should be in git
- **Easy updates**: Developers should update docs easily
- **Professional appearance**: Enterprise-grade look
- **Free hosting**: No infrastructure costs
- **Search**: Users need to find information

### Decision

**MkDocs Material + GitHub Pages:**
- Documentation in markdown (version controlled)
- Material theme (professional appearance)
- GitHub Pages (free hosting)
- Built-in search
- Easy deployment (`mkdocs gh-deploy`)

### Outcome

- **Version controlled**: Docs in git, changes tracked
- **Professional**: Material theme looks enterprise-grade
- **Free**: GitHub Pages is free
- **Easy updates**: Developers edit markdown, deploy automatically
- **Searchable**: Built-in search functionality

### Tradeoffs

**Pros:**
- Free - no hosting costs
- Version controlled - docs in git
- Professional - Material theme looks great
- Easy - markdown is simple
- Searchable - built-in search

**Cons:**
- GitHub dependency - tied to GitHub
- Static only - no dynamic content
- Limited customization - Material theme constraints

**Why we chose this:**
**Documentation should be easy to maintain.** MkDocs + GitHub Pages provides professional documentation with minimal effort. Developers can update docs by editing markdown files.

---

## What env-loader-pro Intentionally Does NOT Solve

### Not a Secret Rotation Tool

**What it does:**
- Loads secrets from rotation-capable sources (Azure Key Vault, AWS Secrets Manager)
- Tracks secret metadata (TTL, rotation status)

**What it doesn't do:**
- Rotate secrets automatically
- Manage secret rotation schedules
- Coordinate rotation across services

**Why:**
Secret rotation is a separate concern. env-loader-pro focuses on **loading** configuration, not **managing** it.

### Not a Configuration Management System

**What it does:**
- Loads configuration from multiple sources
- Merges with deterministic precedence
- Validates configuration

**What it doesn't do:**
- Store configuration in a database
- Provide a UI for editing configuration
- Manage configuration versions
- Coordinate configuration across services

**Why:**
Configuration management (Ansible, Terraform, etc.) is a different problem. env-loader-pro focuses on **runtime loading**, not **configuration management**.

### Not a Service Discovery Tool

**What it does:**
- Loads service endpoints from configuration
- Supports environment-specific endpoints

**What it doesn't do:**
- Discover services automatically
- Manage service registries
- Handle service health checks

**Why:**
Service discovery (Consul, etcd, etc.) is a separate concern. env-loader-pro loads **static configuration**, not **dynamic service discovery**.

### Not a Feature Flag System

**What it does:**
- Loads feature flags as configuration
- Supports environment-specific flags

**What it doesn't do:**
- Provide feature flag UI
- Manage feature flag rollouts
- A/B testing
- Real-time flag updates

**Why:**
Feature flags (LaunchDarkly, etc.) are a specialized domain. env-loader-pro loads **configuration**, not **feature flag logic**.

### Not a Secrets Injection Tool

**What it does:**
- Loads secrets into application memory
- Provides secure access to secrets

**What it doesn't do:**
- Inject secrets into running processes
- Manage secret injection at container level
- Coordinate secret injection across pods

**Why:**
Secret injection (Vault Agent, etc.) is infrastructure-level. env-loader-pro is **application-level** configuration loading.

---

## Design Philosophy Summary

env-loader-pro follows these principles:

1. **Security First**: Secrets win, audit everything, mask by default
2. **Predictability**: Deterministic behavior, no surprises
3. **Simplicity**: Core works everywhere, optional enhancements
4. **Compatibility**: Backward compatible, gradual adoption
5. **Observability**: Audit trails, tracing, performance monitoring
6. **Resilience**: Graceful degradation, failure policies

These principles guide every design decision and tradeoff.
