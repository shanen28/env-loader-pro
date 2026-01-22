# Security Model - env-loader-pro

## 🔒 Security Guarantees

### Secret Handling

**env-loader-pro** is designed with security as a first-class concern:

- ✅ **No secrets in logs** - All secret values are automatically masked
- ✅ **No secrets in exports** - Safe representation used for JSON/YAML export
- ✅ **Audit trail** - Complete provenance tracking without exposing values
- ✅ **Policy enforcement** - Prevent accidental secret exposure
- ✅ **Encrypted lifecycle** - Support for encrypted .env files

## 🎭 Secret Masking

### Automatic Detection

Secrets are automatically detected and masked for keys containing:
- `secret`
- `key`
- `token`
- `password`
- `pwd`
- `credential`
- `auth`
- `api[_-]?key`

### Masking Behavior

```python
config = load_env()

# Safe representation (masked)
safe = config.safe_repr()
# {"API_KEY": "****1234", "PORT": 8080}

# Full access (unmasked, use with caution)
value = config["API_KEY"]  # Full value
```

**Masking Format:**
- Values ≤ 4 chars: Fully masked (`****`)
- Values > 4 chars: Last 4 visible (`****1234`)

### Custom Secret Patterns

```python
from env_loader_pro.utils import mark_as_secret

config = load_env(
    custom_secrets=[mark_as_secret("CUSTOM_SECRET")]
)
```

## 📋 Audit Trail

### What is Tracked

For each configuration variable, the audit trail records:
- **Source**: Where the value came from (azure, aws, system, file, etc.)
- **Provider**: Provider name (if from cloud provider)
- **Masked**: Whether value is treated as secret
- **Timestamp**: When variable was loaded

### What is NOT Tracked

- ❌ **Never stores actual secret values**
- ❌ **Never logs secrets in plaintext**
- ❌ **Never exports secrets in audit JSON**

### Audit Export

```python
config, audit = load_env(audit=True)

# Machine-readable JSON (no secrets)
audit_json = audit.to_json()

# Summary statistics
summary = audit.get_summary()
```

## 🔐 Encrypted .env Files

### Supported Methods

- **age** - Modern encryption tool
- **GPG** - GNU Privacy Guard
- **openssl** - OpenSSL encryption

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

## 🛡️ Policy Enforcement

### Policy-as-Code

Enforce security policies via JSON/YAML:

```yaml
# policy.yaml
require:
  - API_KEY
  - DB_PASSWORD
forbid:
  - DEBUG  # Prevent debug mode in production
sources:
  API_KEY: azure  # Must come from Azure Key Vault
```

```python
config = load_env(policy="policy.yaml")
# Fails if policy violated
```

### Secret Change Detection

```bash
# Fail if secrets added/removed
envloader diff --ci --deny-secret-changes
```

Prevents accidental secret exposure through configuration drift.

## 🔍 CI/CD Safety

### CI-Safe Commands

All CLI commands support `--ci` mode:

```bash
# No cloud access required
envloader validate --ci
envloader audit --ci --json
envloader diff --ci
```

**Guarantees:**
- No network calls to cloud providers
- No credentials required
- Deterministic behavior
- Proper exit codes

## 🚨 Failure Policies

### Per-Provider Error Handling

```python
config = load_env(
    providers=[azure_provider],
    failure_policy={
        "azure": "fail",      # Production: fail on error
        "aws": "fallback",    # Development: continue if unavailable
        "filesystem": "warn"  # Log but don't fail
    }
)
```

**Policies:**
- `fail` - Raise error (production)
- `warn` - Log warning, continue (development)
- `fallback` - Silently continue (resilient)

## 📊 Compliance & Auditing

### Audit Trail for Compliance

The audit trail provides:
- Complete provenance (where each value came from)
- Timestamp of loading
- Provider information
- Masked status

**Use Cases:**
- SOC 2 compliance
- Security audits
- Configuration drift analysis
- Incident investigation

### Export for Auditing

```python
config, audit = load_env(audit=True)

# Export for compliance systems
audit_json = audit.to_json()

# Summary for reports
summary = audit.get_summary()
```

## 🔐 Responsible Disclosure

### Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email: shanen.j.thomas@gmail.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity

### Security Best Practices

1. **Never commit secrets** to version control
2. **Use cloud providers** for production secrets
3. **Enable audit trail** in production
4. **Use policy-as-code** for governance
5. **Enable strict mode** to catch errors early
6. **Review audit logs** regularly
7. **Rotate secrets** according to policy

## ✅ Security Checklist

- [x] Automatic secret masking
- [x] No secrets in logs
- [x] No secrets in exports
- [x] Audit trail (no values)
- [x] Policy enforcement
- [x] Secret change detection
- [x] Encrypted file support
- [x] CI-safe operations
- [x] Failure policies
- [x] Provider capabilities
