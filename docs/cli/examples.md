# CLI Examples

Common use cases and examples.

## Development

### Show Configuration

```bash
# Show current config
envloader show

# Show production config
envloader show --env prod
```

### Validate Configuration

```bash
# Validate required variables
envloader validate --required API_KEY PORT

# Validate with schema
envloader validate --schema config.yaml
```

## Production

### Audit Trail

```bash
# Show audit trail
envloader audit

# Export as JSON
envloader audit --json > audit.json
```

### Configuration Diff

```bash
# Compare with baseline
envloader diff --baseline .env.baseline

# Fail on secret changes
envloader diff --deny-secret-changes --baseline .env.baseline
```

## CI/CD

### Validation

```bash
# CI-safe validation
envloader validate --ci --required API_KEY PORT
```

### Audit

```bash
# CI-safe audit
envloader audit --ci --json > audit.json
```

### Diff

```bash
# CI-safe diff
envloader diff --ci --deny-secret-changes --baseline .env.baseline
```

## Encryption

### Encrypt

```bash
# Encrypt .env file
envloader encrypt .env

# Encrypt with specific method
envloader encrypt .env --method gpg
```

### Decrypt

```bash
# Decrypt .env.enc
envloader decrypt .env.enc
```

## Export

### Export to JSON

```bash
envloader export --output config.json --format json
```

### Export to YAML

```bash
envloader export --output config.yaml --format yaml
```

## Generate Example

```bash
# Generate .env.example
envloader generate-example --required API_KEY PORT --optional DEBUG
```

## Related Topics

- [CLI Commands](../cli/commands.md)
