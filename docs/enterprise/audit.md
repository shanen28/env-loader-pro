# Audit Trail

Complete provenance tracking for compliance, debugging, and security audits. The audit trail records where each configuration variable came from **without storing secret values**.

## Overview

The audit trail provides:
- **Source tracking**: Where each variable came from (azure, aws, system, file, etc.)
- **Provider information**: Which provider supplied the value (if applicable)
- **Masking status**: Whether the value is treated as a secret
- **Timestamp**: When the variable was loaded
- **No secret values**: Never stores actual secret values

## Enable Audit Trail

Enable audit trail by setting `audit=True`:

```python
from env_loader_pro import load_env

# Enable audit
config, audit = load_env(audit=True)

# Use configuration normally
port = config["PORT"]
api_key = config["API_KEY"]

# Access audit log
print(audit.to_json())
```

!!! note "Return Type"
    When `audit=True`, `load_env()` returns a tuple: `(config, audit)`. When `audit=False` (default), it returns just `config`.

## What is Tracked

For each configuration variable, the audit trail records:

| Field | Description | Example |
|-------|-------------|---------|
| `key` | Variable name | `"API_KEY"` |
| `source` | Source origin | `"azure"`, `"aws"`, `"system"`, `"file"` |
| `provider` | Provider name (if from provider) | `"AzureKeyVaultProvider"` |
| `masked` | Whether value is treated as secret | `true` or `false` |
| `timestamp` | When variable was loaded | `"2024-01-15T10:30:00Z"` |

## What is NOT Tracked

The audit trail **never** stores:
- ❌ **Actual secret values** - Only metadata
- ❌ **Plaintext passwords** - Only masked status
- ❌ **Configuration values** - Only provenance

!!! danger "Security Guarantee"
    The audit trail is **safe to log, export, and store**. It contains no secret values, only metadata about where values came from.

## Accessing Audit Data

### Get Entry for Variable

Get audit information for a specific variable:

```python
config, audit = load_env(audit=True)

entry = audit.get("API_KEY")
if entry:
    print(f"Source: {entry.source}")        # "azure"
    print(f"Provider: {entry.provider}")     # "AzureKeyVaultProvider"
    print(f"Masked: {entry.masked}")         # True
    print(f"Timestamp: {entry.timestamp}")   # datetime object
```

### Export as JSON

Export the entire audit trail as JSON:

```python
config, audit = load_env(audit=True)

# Export as JSON string
audit_json = audit.to_json()
print(audit_json)

# With custom indentation
audit_json = audit.to_json(indent=4)
```

**Example JSON Output:**

```json
{
  "API_KEY": {
    "key": "API_KEY",
    "source": "azure",
    "provider": "AzureKeyVaultProvider",
    "masked": true,
    "timestamp": "2024-01-15T10:30:00.123456"
  },
  "PORT": {
    "key": "PORT",
    "source": "file",
    "provider": null,
    "masked": false,
    "timestamp": "2024-01-15T10:30:00.123456"
  },
  "DB_PASSWORD": {
    "key": "DB_PASSWORD",
    "source": "aws",
    "provider": "AWSSecretsManagerProvider",
    "masked": true,
    "timestamp": "2024-01-15T10:30:00.123456"
  }
}
```

### Get Summary Statistics

Get summary statistics about the audit trail:

```python
config, audit = load_env(audit=True)

summary = audit.get_summary()
print(summary)
```

**Example Summary:**

```json
{
  "total_variables": 10,
  "masked_variables": 3,
  "sources": {
    "azure": 2,
    "aws": 1,
    "system": 3,
    "file": 4
  },
  "providers": {
    "AzureKeyVaultProvider": 2,
    "AWSSecretsManagerProvider": 1
  }
}
```

### Get Entries by Source

Filter entries by source:

```python
config, audit = load_env(audit=True)

# Get all entries from Azure
azure_entries = audit.get_by_source("azure")
# Returns: {"API_KEY": AuditEntry, "DB_PASSWORD": AuditEntry}

# Get all entries from files
file_entries = audit.get_by_source("file")
```

## Source Values

The `source` field can have these values:

| Source | Description | Example |
|--------|-------------|---------|
| `azure` | Azure Key Vault | Secrets from Azure |
| `aws` | AWS Secrets Manager | Secrets from AWS |
| `system` | System environment | `os.environ` |
| `docker` | Docker secrets | `/run/secrets` |
| `k8s` | Kubernetes secrets | `/etc/secrets` |
| `file.env` | Environment-specific file | `.env.prod` |
| `file` | Base .env file | `.env` |
| `schema_default` | Schema default value | Default from schema |

## CLI Usage

### Show Audit Trail

```bash
# Show audit trail (human-readable)
envloader audit

# Export as JSON
envloader audit --json

# CI-safe mode (no cloud access)
envloader audit --ci --json
```

### Example CLI Output

```bash
$ envloader audit --json
{
  "API_KEY": {
    "key": "API_KEY",
    "source": "azure",
    "provider": "AzureKeyVaultProvider",
    "masked": true,
    "timestamp": "2024-01-15T10:30:00.123456"
  },
  "PORT": {
    "key": "PORT",
    "source": "file",
    "provider": null,
    "masked": false,
    "timestamp": "2024-01-15T10:30:00.123456"
  }
}
```

## Use Cases

### Compliance

Export audit trail for compliance systems:

```python
config, audit = load_env(audit=True)

# Export for compliance systems
with open("audit.json", "w") as f:
    f.write(audit.to_json())

# Or send to compliance API
import requests
requests.post("https://compliance-api/audit", json=audit.to_dict())
```

### Debugging

Find where a variable came from:

```python
config, audit = load_env(audit=True)

# Find where DB_PASSWORD came from
entry = audit.get("DB_PASSWORD")
if entry:
    print(f"DB_PASSWORD came from: {entry.source}")
    print(f"Provider: {entry.provider}")
    print(f"Loaded at: {entry.timestamp}")
```

### Security Audits

Check if secrets are from secure sources:

```python
config, audit = load_env(audit=True)

# Check if secrets are from secure sources
for key, entry in audit.entries.items():
    if entry.masked:
        if entry.source not in ["azure", "aws"]:
            print(f"Warning: Secret {key} not from secure source (came from {entry.source})")
```

### Configuration Drift Analysis

Track configuration changes over time:

```python
# Save audit from previous deployment
previous_audit = load_previous_audit()

# Current audit
config, current_audit = load_env(audit=True)

# Compare sources
for key, entry in current_audit.entries.items():
    prev_entry = previous_audit.get(key)
    if prev_entry and prev_entry.source != entry.source:
        print(f"Warning: {key} source changed from {prev_entry.source} to {entry.source}")
```

## Best Practices

### 1. Enable Audit in Production

Always enable audit trail in production for compliance:

```python
# Production configuration
config, audit = load_env(
    env="prod",
    providers=[azure_provider],
    audit=True  # Enable audit
)
```

### 2. Export Regularly

Export audit logs regularly for compliance:

```python
config, audit = load_env(audit=True)

# Export to file
with open(f"audit-{datetime.now().isoformat()}.json", "w") as f:
    f.write(audit.to_json())
```

### 3. Review Sources

Regularly review audit logs to ensure secrets from secure sources:

```python
config, audit = load_env(audit=True)

summary = audit.get_summary()
if summary["sources"].get("file", 0) > 0:
    # Check if any secrets came from files
    file_secrets = [
        k for k, e in audit.entries.items()
        if e.masked and e.source == "file"
    ]
    if file_secrets:
        print(f"Warning: Secrets from files: {file_secrets}")
```

### 4. Use CI-Safe Mode

In CI pipelines, use CI-safe mode:

```bash
# CI pipeline
envloader audit --ci --json > audit.json
```

### 5. Store Audit Logs Separately

Store audit logs separately from application logs:

```python
config, audit = load_env(audit=True)

# Store in separate audit log system
send_to_audit_system(audit.to_dict())
```

## Integration Examples

### Logging Integration

```python
import logging
from env_loader_pro import load_env

config, audit = load_env(audit=True)

# Log audit summary (safe, no secrets)
logging.info("Configuration loaded", extra={
    "audit_summary": audit.get_summary()
})
```

### Monitoring Integration

```python
from env_loader_pro import load_env
import prometheus_client

config, audit = load_env(audit=True)

# Track configuration sources
for source, count in audit.get_summary()["sources"].items():
    prometheus_client.Counter(
        "config_source_total",
        "Configuration variables by source",
        ["source"]
    ).labels(source=source).inc(count)
```

### Compliance API Integration

```python
from env_loader_pro import load_env
import requests

config, audit = load_env(audit=True)

# Send to compliance API
response = requests.post(
    "https://compliance-api.example.com/audit",
    json=audit.to_dict(),
    headers={"Authorization": "Bearer ..."}
)
```

## Related Topics

- [Security Model](../security/model.md) - Security guarantees
- [Configuration Precedence](../core-concepts/precedence.md) - How sources are merged
- [CLI Commands](../cli/commands.md) - CLI audit commands
