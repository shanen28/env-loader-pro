# CLI Commands

Complete reference for the `envloader` command-line tool. All commands support CI-safe mode with `--ci` flag.

## Command Overview

| Command | Description | CI-Safe |
|---------|-------------|---------|
| `show` | Display environment variables | ✅ |
| `validate` | Validate configuration | ✅ |
| `audit` | Show audit trail | ✅ |
| `diff` | Compare configurations | ✅ |
| `explain` | Explain precedence | ✅ |
| `export` | Export to JSON/YAML | ✅ |
| `generate-example` | Generate .env.example | ✅ |
| `encrypt` | Encrypt .env file | ✅ |
| `decrypt` | Decrypt .env file | ✅ |

## show

Display environment variables in various formats.

### Syntax

```bash
envloader show [--env ENV] [--path PATH] [--format FORMAT] [--unmask]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name (e.g., prod, dev) | None |
| `--path PATH` | Path to .env file | `.env` |
| `--format FORMAT` | Output format: `json`, `yaml`, `pretty` | `pretty` |
| `--unmask` | Show unmasked secret values (dangerous!) | False |

### Examples

```bash
# Show current config (pretty format)
envloader show

# Show production config
envloader show --env prod

# Export as JSON
envloader show --format json

# Export as YAML
envloader show --format yaml

# Show unmasked values (dangerous!)
envloader show --unmask
```

!!! danger "Unmask Flag"
    The `--unmask` flag shows secret values in plaintext. **Never use in production or CI/CD pipelines.**

### Exit Codes

- `0` - Success
- `1` - Error (file not found, parsing error, etc.)

## validate

Validate environment configuration. This command is **CI-safe** by default when using `--ci` flag.

### Syntax

```bash
envloader validate [--env ENV] [--path PATH] [--required VAR ...] [--ci] [--strict]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name | None |
| `--path PATH` | Path to .env file | `.env` |
| `--required VAR` | Required variables (can specify multiple) | None |
| `--ci` | CI mode: no cloud access, fail on errors | False |
| `--strict` | Enable strict mode (warn on unknown vars) | False |

### Examples

```bash
# Basic validation
envloader validate

# Validate with required variables
envloader validate --required API_KEY PORT DB_URI

# CI-safe validation (no cloud access)
envloader validate --ci --required API_KEY PORT

# Strict mode (warn on unknown variables)
envloader validate --strict
```

### CI Mode Behavior

When `--ci` flag is used:
- ✅ **No cloud providers accessed** (providers list is empty)
- ✅ **No network calls** to Azure/AWS
- ✅ **Deterministic behavior** (same result every time)
- ✅ **Proper exit codes** (0 = success, non-zero = failure)

### Exit Codes

- `0` - Validation passed
- `1` - Validation failed (missing required vars, type errors, etc.)
- `2` - Configuration error (file not found, etc.)

### Example Output

```bash
$ envloader validate --required API_KEY PORT
✓ Validation passed
Found 15 environment variables

$ envloader validate --required MISSING_VAR
✗ Validation failed: Missing required environment variables: MISSING_VAR
```

## audit

Show configuration audit trail with provenance information.

### Syntax

```bash
envloader audit [--env ENV] [--path PATH] [--json] [--ci]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name | None |
| `--path PATH` | Path to .env file | `.env` |
| `--json` | Output as JSON | False (human-readable) |
| `--ci` | CI mode: no cloud access | False |

### Examples

```bash
# Show audit trail (human-readable)
envloader audit

# Export as JSON
envloader audit --json

# CI-safe audit
envloader audit --ci --json

# Production audit
envloader audit --env prod --json
```

### Exit Codes

- `0` - Success
- `1` - Error (file not found, etc.)

### Example Output

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

## diff

Compare current configuration with a baseline to detect changes.

### Syntax

```bash
envloader diff [--env ENV] [--path PATH] [--baseline PATH] [--deny-secret-changes] [--deny-added-secrets] [--ci]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name | None |
| `--path PATH` | Path to .env file | `.env` |
| `--baseline PATH` | Baseline configuration file (JSON/YAML) | None |
| `--deny-secret-changes` | Fail if secrets added/removed/changed | False |
| `--deny-added-secrets` | Fail if new secrets added | False |
| `--ci` | CI mode: no cloud access | False |

### Examples

```bash
# Compare with baseline
envloader diff --baseline .env.baseline

# Fail on secret changes (CI/CD)
envloader diff --ci --deny-secret-changes --baseline .env.baseline

# Fail if new secrets added
envloader diff --ci --deny-added-secrets --baseline .env.baseline
```

### Exit Codes

- `0` - No changes or changes allowed
- `1` - Changes detected and denied (with `--deny-*` flags)
- `2` - Error (baseline not found, etc.)

### Example Output

```bash
$ envloader diff --baseline .env.baseline
Added variables:
  - NEW_VAR: "value"

Changed variables:
  - PORT: "8080" → "9000"

Removed variables:
  - OLD_VAR: "value"
```

## explain

Explain configuration precedence and failure policies.

### Syntax

```bash
envloader explain [--env ENV] [--path PATH] [--format FORMAT]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name | None |
| `--path PATH` | Path to .env file | `.env` |
| `--format FORMAT` | Output format: `text`, `json` | `text` |

### Examples

```bash
# Explain precedence (human-readable)
envloader explain

# Export as JSON
envloader explain --format json

# Production explanation
envloader explain --env prod
```

### Exit Codes

- `0` - Success
- `1` - Error

### Example Output

```bash
$ envloader explain
======================================================================
CONFIGURATION PRECEDENCE & POLICIES
======================================================================

Resolution Order (highest to lowest priority):

  1. Cloud providers (Azure Key Vault, AWS Secrets Manager)
     Source: cloud_providers

  2. System environment variables
     Source: system

  3. Docker/K8s mounted secrets
     Source: docker_k8s

  4. .env.prod (environment-specific file)
     Source: env_specific

  5. Base .env file
     Source: base_file

  6. Schema default values
     Source: schema_defaults

Failure Policies (default):
  azure              : fail        (Raise error on failure)
  aws                : fallback    (Silently continue (use fallback))
  filesystem         : warn        (Log warning and continue)
  docker             : warn        (Log warning and continue)
  kubernetes         : warn        (Log warning and continue)

Note: Later sources override earlier ones in case of conflicts.
      Cloud providers have highest priority (secrets win).
```

## export

Export configuration to JSON or YAML file.

### Syntax

```bash
envloader export [--env ENV] [--path PATH] [--output PATH] [--format FORMAT]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env ENV` | Environment name | None |
| `--path PATH` | Path to .env file | `.env` |
| `--output PATH` | Output file path (required) | None |
| `--format FORMAT` | Output format: `json`, `yaml` | `json` |

### Examples

```bash
# Export to JSON
envloader export --output config.json --format json

# Export to YAML
envloader export --output config.yaml --format yaml

# Export production config
envloader export --env prod --output config.prod.json
```

!!! note "Export Safety"
    Exported files use `safe_repr()` by default, which masks secrets. This is safe to commit to version control.

### Exit Codes

- `0` - Success
- `1` - Error (file write error, etc.)

## generate-example

Generate a `.env.example` file from required and optional variables.

### Syntax

```bash
envloader generate-example [--output PATH] [--required VAR ...] [--optional VAR ...]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output PATH` | Output file path | `.env.example` |
| `--required VAR` | Required variables (can specify multiple) | None |
| `--optional VAR` | Optional variables (can specify multiple) | None |

### Examples

```bash
# Generate .env.example
envloader generate-example --required API_KEY PORT --optional DEBUG

# Custom output path
envloader generate-example --output .env.template --required DB_URI
```

### Exit Codes

- `0` - Success
- `1` - Error (file write error, etc.)

### Example Output

```bash
$ envloader generate-example --required API_KEY PORT --optional DEBUG
Generated .env.example
```

Generated `.env.example`:
```bash
# Required variables
API_KEY=
PORT=

# Optional variables
DEBUG=
```

## encrypt

Encrypt a `.env` file using age or GPG.

### Syntax

```bash
envloader encrypt INPUT [--output OUTPUT] [--method METHOD] [--key PATH]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `INPUT` | Input file path (required) | None |
| `--output OUTPUT` | Output file path | `INPUT.enc` |
| `--method METHOD` | Encryption method: `age`, `gpg` | `age` |
| `--key PATH` | Path to encryption key | None (uses default) |

### Examples

```bash
# Encrypt .env file
envloader encrypt .env

# Encrypt with specific method
envloader encrypt .env --method gpg

# Specify output file
envloader encrypt .env --output .env.encrypted

# Use custom key
envloader encrypt .env --key /path/to/key
```

### Exit Codes

- `0` - Success
- `1` - Error (file not found, encryption error, etc.)

## decrypt

Decrypt an encrypted `.env` file.

### Syntax

```bash
envloader decrypt INPUT [--output OUTPUT] [--key PATH]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `INPUT` | Input encrypted file path (required) | None |
| `--output OUTPUT` | Output file path | `INPUT` without `.enc` |
| `--key PATH` | Path to decryption key | None (uses default) |

### Examples

```bash
# Decrypt .env.enc
envloader decrypt .env.enc

# Specify output file
envloader decrypt .env.enc --output .env

# Use custom key
envloader decrypt .env.enc --key /path/to/key
```

!!! warning "Decryption Safety"
    Decrypted files contain plaintext secrets. **Never commit decrypted files to version control.**

### Exit Codes

- `0` - Success
- `1` - Error (file not found, decryption error, etc.)

## Global Options

All commands support these global options (via environment variables):

| Variable | Description |
|----------|-------------|
| `ENVLOADER_VERBOSE` | Enable verbose output |
| `ENVLOADER_LOG_LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |

## Exit Code Summary

| Code | Meaning | Commands |
|------|---------|----------|
| `0` | Success | All commands |
| `1` | General error | All commands |
| `2` | Validation/configuration error | `validate`, `diff` |

## CI/CD Integration

All commands support `--ci` flag for CI/CD pipelines:

```bash
# CI pipeline example
envloader validate --ci --required API_KEY PORT
envloader audit --ci --json > audit.json
envloader diff --ci --deny-secret-changes --baseline .env.baseline
```

!!! tip "CI Mode Benefits"
    - No cloud access required
    - Deterministic behavior
    - Proper exit codes for pipeline control
    - Fast execution (no network calls)

## Related Topics

- [CLI Examples](../cli/examples.md) - Common use cases
- [CI/CD Safety](../security/ci-safety.md) - CI-safe operations
