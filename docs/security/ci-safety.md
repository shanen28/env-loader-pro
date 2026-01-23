# CI/CD Safety

All CLI commands work without cloud credentials, perfect for CI pipelines.

## CI-Safe Commands

All commands support `--ci` flag:

```bash
# Validate (no cloud access)
envloader validate --ci --required API_KEY PORT

# Audit (no cloud access)
envloader audit --ci --json

# Diff (no cloud access)
envloader diff --ci --deny-secret-changes

# Explain (no cloud access)
envloader explain --ci
```

## Guarantees

When using `--ci` flag:

- ✅ **No network calls** to cloud providers
- ✅ **No credentials required**
- ✅ **Deterministic behavior**
- ✅ **Proper exit codes** (0 = success, non-zero = failure)

## CI Pipeline Example

### GitHub Actions

```yaml
name: Validate Config

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install env-loader-pro
      - run: envloader validate --ci --required API_KEY PORT
      - run: envloader audit --ci --json > audit.json
      - run: envloader diff --ci --deny-secret-changes
```

### GitLab CI

```yaml
validate:
  image: python:3.8
  script:
    - pip install env-loader-pro
    - envloader validate --ci --required API_KEY PORT
    - envloader audit --ci --json
```

## Validation in CI

### Schema Validation

```bash
# Validate schema without cloud access
envloader validate --ci --schema config.yaml
```

### Required Variables

```bash
# Check required variables exist
envloader validate --ci --required API_KEY DB_PASSWORD
```

## Audit in CI

### Export Audit

```bash
# Export audit for compliance
envloader audit --ci --json > audit.json

# Upload to artifact storage
```

## Diff in CI

### Prevent Secret Changes

```bash
# Fail if secrets changed
envloader diff --ci --deny-secret-changes --baseline .env.baseline
```

### Prevent Added Secrets

```bash
# Fail if new secrets added
envloader diff --ci --deny-added-secrets --baseline .env.baseline
```

## Best Practices

1. **Always use `--ci` flag** in CI pipelines
2. **Validate early** in pipeline
3. **Export audit logs** for compliance
4. **Check for secret changes** before deployment
5. **Use exit codes** for pipeline control

## Related Topics

- [Security Model](../security/model.md)
- [Configuration Diff](../enterprise/diff.md)
