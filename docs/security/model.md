# Security Model

Complete security guarantees and secret handling for env-loader-pro. This document explains the security model, guarantees, and how secrets are protected throughout the configuration lifecycle.

## Security Guarantees

env-loader-pro is designed with **security as a first-class concern**. These guarantees are non-negotiable and enforced at every level:

- ✅ **No secrets in logs** - All secret values are automatically masked
- ✅ **No secrets in exports** - Safe representation used for JSON/YAML export
- ✅ **Audit trail** - Complete provenance tracking without exposing values
- ✅ **Policy enforcement** - Prevent accidental secret exposure
- ✅ **Encrypted lifecycle** - Support for encrypted .env files
- ✅ **CI/CD safe** - Validation works without cloud credentials
- ✅ **Memory safety** - Secrets never persisted to disk unnecessarily

## Secret Handling

### Automatic Detection

Secrets are automatically detected and masked for keys matching these patterns (case-insensitive):

- `secret` - Any key containing "secret"
- `key` - Any key containing "key"
- `token` - Any key containing "token"
- `password` - Any key containing "password"
- `pwd` - Any key containing "pwd"
- `credential` - Any key containing "credential"
- `auth` - Any key containing "auth"
- `api[_-]?key` - API key patterns (e.g., `API_KEY`, `API-KEY`)

**Examples:**
```python
# These are automatically detected as secrets:
API_KEY=secret123          # ✅ Detected (contains "key")
DB_PASSWORD=pass123        # ✅ Detected (contains "password")
AUTH_TOKEN=token123       # ✅ Detected (contains "token")
SECRET_VALUE=value123     # ✅ Detected (contains "secret")

# These are NOT detected:
PORT=8080                 # ❌ Not a secret
DEBUG=true                 # ❌ Not a secret
HOST=localhost             # ❌ Not a secret
```

### Masking Behavior

```python
config = load_env()

# Safe representation (masked)
safe = config.safe_repr()
# {"API_KEY": "****1234", "PORT": 8080, "DB_PASSWORD": "****"}

# Full access (unmasked, use with caution)
value = config["API_KEY"]  # Full value
```

**Masking Format:**
- **Values ≤ 4 chars**: Fully masked (`****`)
- **Values > 4 chars**: Last 4 visible (`****1234`)

**Rationale:**
- Short values fully masked (no information leakage)
- Long values show last 4 chars (helps debugging without exposing full secret)
- Consistent format across all outputs

### Custom Secret Patterns

Mark additional keys as secrets:

```python
from env_loader_pro.utils import mark_as_secret

config = load_env(
    custom_secrets=[
        mark_as_secret("CUSTOM_SECRET"),
        mark_as_secret("INTERNAL_TOKEN")
    ]
)
```

### Pattern Matching

Check if a key is treated as a secret:

```python
from env_loader_pro.utils import is_secret_key

if is_secret_key("MY_API_KEY"):
    print("This is a secret")
```

## Audit Trail Security

### What is Tracked

For each configuration variable, the audit trail records:
- **Source**: Where the value came from (azure, aws, system, file, etc.)
- **Provider**: Provider name (if from cloud provider)
- **Masked**: Whether value is treated as secret
- **Timestamp**: When variable was loaded

### What is NOT Tracked

**Critical security guarantee:**
- ❌ **Never stores actual secret values**
- ❌ **Never logs secrets in plaintext**
- ❌ **Never exports secrets in audit JSON**
- ❌ **Never includes secrets in audit summaries**

**Example audit entry:**
```json
{
  "API_KEY": {
    "key": "API_KEY",
    "source": "azure",
    "provider": "AzureKeyVaultProvider",
    "masked": true,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Note**: The actual value of `API_KEY` is **never** in the audit trail.

## Encrypted .env Files

### Supported Methods

- **age** - Modern encryption tool (recommended)
- **GPG** - GNU Privacy Guard (widely supported)
- **openssl** - OpenSSL encryption (universal)

### Lifecycle

```bash
# Encrypt
envloader encrypt .env --method age

# Decrypt (never stores plaintext on disk)
envloader decrypt .env.enc

# Load encrypted
config = load_env(path=".env.enc", encrypted=True)
```

**Guarantee**: Plaintext is never persisted to disk during encrypt/decrypt operations.

**Security properties:**
- Encryption happens in memory
- Plaintext never written to disk
- Decryption happens at load time
- Keys managed separately

## Policy Enforcement

### Policy-as-Code

Enforce security policies via JSON/YAML:

```yaml
# policy.yaml
security:
  require_cloud_secrets: true
  forbid_local_secrets: ["DB_PASSWORD", "API_KEY"]
  require_encryption: true
```

**Enforcement:**
- Policies checked at load time
- Violations raise `PolicyError`
- Can be enforced in CI/CD

### Strict Mode

Prevent accidental loading of unknown variables:

```python
config = load_env(
    strict=True  # Fails if unknown variables found
)
```

**Security benefit**: Prevents loading of potentially malicious or misconfigured variables.

## Memory Safety

### Secrets in Memory

**Guarantee**: Secrets are only in memory during application runtime.

- Secrets loaded into memory at startup
- Never persisted to disk (unless explicitly encrypted)
- Memory cleared when process exits
- No swap file exposure (OS-level concern)

### Safe Exports

```python
config = load_env()

# Safe export (secrets masked)
config.save("config.json", format="json", safe=True)

# Unsafe export (secrets exposed) - NOT RECOMMENDED
config.save("config.json", format="json", safe=False)  # ⚠️ Dangerous
```

## Logging Safety

### Safe Logging

```python
import logging

config = load_env()

# ✅ SAFE: Secrets masked
logging.info(f"Config: {config.safe_repr()}")
# Output: Config: {"API_KEY": "****1234", "PORT": 8080}

# ❌ UNSAFE: Secrets exposed
logging.info(f"API Key: {config['API_KEY']}")  # Never do this!
```

### Best Practices

1. **Always use `safe_repr()`** for logging
2. **Never log secrets directly**
3. **Review logs** to ensure no secrets leaked
4. **Use structured logging** with safe serialization
5. **Enable audit trail** to track secret access

## CI/CD Safety

### No Cloud Credentials Needed

CI pipelines can validate configuration without cloud credentials:

```bash
# CI validation (no cloud access)
envloader validate --ci --required API_KEY PORT
```

**Security benefits:**
- No production credentials in CI
- Fast validation (no network calls)
- Deterministic behavior
- Proper exit codes

### CI-Safe Mode

```python
# CI-safe mode disables cloud providers
config = load_env(
    providers=[],  # No cloud providers in CI
    env="ci"
)
```

## Threat Model

### What env-loader-pro Protects Against

✅ **Secret leakage in logs** - Automatic masking
✅ **Accidental secret commits** - Encrypted configs
✅ **Unauthorized configuration** - Strict mode
✅ **Configuration drift** - Audit trail
✅ **Cloud provider failures** - Failure policies

### What env-loader-pro Does NOT Protect Against

❌ **Memory dumps** - OS-level concern
❌ **Swap file exposure** - OS-level concern
❌ **Process inspection** - OS-level concern
❌ **Network interception** - Transport-level concern
❌ **Cloud provider breaches** - Provider-level concern

**Rationale**: env-loader-pro focuses on **application-level** security. OS-level and transport-level security are separate concerns.

## Compliance

### SOC 2

- ✅ **Audit trail** - Complete provenance tracking
- ✅ **Access control** - Policy enforcement
- ✅ **Encryption** - Encrypted config support
- ✅ **Logging** - Safe logging practices

### HIPAA

- ✅ **Secret masking** - No secrets in logs
- ✅ **Audit trail** - Complete access tracking
- ✅ **Encryption** - Encrypted config support

### GDPR

- ✅ **Data minimization** - Only load what's needed
- ✅ **Audit trail** - Track data access
- ✅ **Encryption** - Encrypted config support

## Security Best Practices

### 1. Use Cloud Providers for Secrets

```python
# ✅ GOOD: Secrets from cloud
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}  # Fail if unavailable
)

# ❌ BAD: Secrets in .env files
# .env: API_KEY=secret123  # Don't do this!
```

### 2. Enable Audit Trail

```python
# ✅ GOOD: Track secret access
config, audit = load_env(audit=True)

# ❌ BAD: No audit trail
config = load_env()  # No tracking
```

### 3. Use Strict Mode

```python
# ✅ GOOD: Prevent unknown variables
config = load_env(strict=True)

# ❌ BAD: Allow unknown variables
config = load_env(strict=False)  # Might load malicious config
```

### 4. Encrypt Sensitive Configs

```bash
# ✅ GOOD: Encrypted configs
envloader encrypt .env --method age

# ❌ BAD: Plaintext configs
# .env: API_KEY=secret123  # Plaintext on disk
```

### 5. Use CI-Safe Validation

```bash
# ✅ GOOD: CI validation without credentials
envloader validate --ci --required API_KEY

# ❌ BAD: CI with cloud credentials
envloader validate --required API_KEY  # Needs cloud access
```

## Related Topics

- [Secret Masking](../security/masking.md) - Detailed masking behavior
- [Encrypted Files](../security/encryption.md) - Encryption lifecycle
- [CI/CD Safety](../security/ci-safety.md) - CI/CD security
- [Audit Trail](../enterprise/audit.md) - Audit trail details
