# Tradeoffs and Real-World Scenarios

This document explains tradeoffs in env-loader-pro's design and how they play out in real-world scenarios.

## Precedence: Security vs Flexibility

### The Tradeoff

**Fixed precedence** (security-first) vs **configurable precedence** (flexibility).

### Real-World Scenario: Production Outage

**Scenario**: Azure Key Vault is down. Application needs to start.

**With fixed precedence:**
- Application fails to start (if Azure is required)
- Clear error: "Azure Key Vault unavailable"
- No ambiguity about what happened

**With configurable precedence:**
- Could fall back to `.env` file
- Application starts with potentially wrong config
- Silent failure - might not notice until later

**Our choice**: Fixed precedence with explicit failure policies.

```python
# Production: fail fast
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "fail"}
)

# Development: resilient
config = load_env(
    providers=[azure_provider],
    failure_policy={"azure": "warn"}  # Log but continue
)
```

**Why**: In production, **failures should be loud**. Silent fallbacks hide problems.

---

## Audit Trail: Performance vs Compliance

### The Tradeoff

**Per-variable audit trail** (compliance) vs **no audit trail** (performance).

### Real-World Scenario: Security Audit

**Scenario**: SOC 2 audit requires proving where secrets came from.

**Without audit trail:**
- Can't prove secrets came from secure sources
- Audit fails
- Must implement custom logging

**With audit trail:**
- Complete provenance for every variable
- JSON export for compliance systems
- Audit passes

**Performance impact:**
- Memory: ~100 bytes per variable (negligible)
- CPU: < 1ms overhead (negligible)
- Disk: Only if exported (optional)

**Our choice**: Per-variable audit trail, enabled by default in production.

```python
# Production: always audit
config, audit = load_env(audit=True)

# Export for compliance
with open("audit.json", "w") as f:
    f.write(audit.to_json())
```

**Why**: **Compliance is non-negotiable.** The performance cost is negligible compared to the value.

---

## Cloud SDKs: Optional vs Required

### The Tradeoff

**Optional cloud SDKs** (flexibility) vs **required cloud SDKs** (simplicity).

### Real-World Scenario: CI Pipeline

**Scenario**: CI pipeline needs to validate configuration.

**With required cloud SDKs:**
- Must install `boto3`, `azure-identity` in CI
- Must provide cloud credentials
- Slow installation, security risk

**With optional cloud SDKs:**
- CI validation works without cloud SDKs
- No cloud credentials needed
- Fast, secure

**Our choice**: Optional cloud SDKs with graceful degradation.

```python
# CI pipeline (no cloud SDKs needed)
envloader validate --ci --required API_KEY PORT

# Production (with cloud SDKs)
config = load_env(providers=[azure_provider])
```

**Why**: **CI pipelines should be fast and secure.** They shouldn't need production credentials.

---

## Failure Policies: Explicit vs Implicit

### The Tradeoff

**Explicit failure policies** (clarity) vs **implicit behavior** (simplicity).

### Real-World Scenario: Network Outage

**Scenario**: Azure Key Vault is unreachable due to network issue.

**With implicit behavior:**
- Unclear what happens
- Might fail, might continue
- Hard to debug

**With explicit policies:**
- Clear behavior per provider
- Environment-specific policies
- Easy to debug

**Our choice**: Explicit per-provider failure policies.

```python
# Production: fail fast
failure_policy = {"azure": "fail"}

# Development: resilient
failure_policy = {"azure": "warn"}
```

**Why**: **Explicit is better than implicit.** Developers should know exactly what happens on failure.

---

## Caching: Performance vs Freshness

### The Tradeoff

**Caching** (performance) vs **always fresh** (accuracy).

### Real-World Scenario: Secret Rotation

**Scenario**: Secret rotated in Azure Key Vault. Application still using cached value.

**With no caching:**
- Always fresh values
- Slow (API call every time)
- Rate limit issues

**With caching:**
- Fast (cached values)
- Might use stale values
- Must respect TTL

**Our choice**: Caching with TTL, respect secret metadata.

```python
config = load_env(
    providers=[azure_provider],
    cache=True,
    cache_ttl=3600  # 1 hour
)

# Provider can return TTL metadata
# Cache respects TTL, reloads when expired
```

**Why**: **Performance matters, but freshness is configurable.** Most secrets don't rotate frequently.

---

## CI-Safe Mode: Validation vs Completeness

### The Tradeoff

**CI-safe validation** (security) vs **full validation** (completeness).

### Real-World Scenario: Pre-deployment Validation

**Scenario**: CI pipeline validates configuration before deployment.

**Without CI-safe mode:**
- Must provide cloud credentials
- Security risk
- Slow (network calls)

**With CI-safe mode:**
- No cloud credentials needed
- Fast validation
- Validates local sources only

**Our choice**: CI-safe mode for validation, full mode for runtime.

```bash
# CI: validate without cloud
envloader validate --ci --required API_KEY PORT

# Runtime: full validation with cloud
config = load_env(providers=[azure_provider])
```

**Why**: **CI should validate what it can, without security risks.** Runtime can use full validation.

---

## Encrypted Configs: Security vs Complexity

### The Tradeoff

**Encrypted configs** (security) vs **plaintext configs** (simplicity).

### Real-World Scenario: Developer Laptop

**Scenario**: Developer laptop stolen. `.env` file contains production secrets.

**With plaintext:**
- Secrets exposed
- Must rotate all secrets
- Security incident

**With encrypted:**
- Secrets encrypted
- Need key to decrypt
- Reduced risk

**Our choice**: Support encrypted configs, but don't require them.

```bash
# Encrypt for version control
envloader encrypt .env --method age

# Can commit encrypted file
git add .env.enc
```

**Why**: **Security should be opt-in, not forced.** Teams can choose based on their needs.

---

## Backward Compatibility: Stability vs Clean API

### The Tradeoff

**Backward compatibility** (stability) vs **clean API** (simplicity).

### Real-World Scenario: Library Upgrade

**Scenario**: Upgrading env-loader-pro in production application.

**With breaking changes:**
- Must rewrite code
- Risk of bugs
- Deployment complexity

**With backward compatibility:**
- Existing code works
- Can adopt new features gradually
- Low-risk upgrade

**Our choice**: Full backward compatibility, new features are additive.

```python
# Old code still works
config = load_env(required=["API_KEY"])

# Can adopt new features gradually
config, audit = load_env(required=["API_KEY"], audit=True)
```

**Why**: **Stability is more important than API purity.** Breaking changes hurt adoption.

---

## Performance Guarantees: SLAs vs Flexibility

### The Tradeoff

**Performance SLAs** (predictability) vs **no guarantees** (flexibility).

### Real-World Scenario: Cold Start

**Scenario**: Application cold start in serverless function.

**Without SLAs:**
- Unpredictable performance
- Might timeout
- Hard to debug

**With SLAs:**
- Documented performance targets
- Warnings if breached
- Predictable behavior

**Our choice**: Performance SLAs with monitoring.

```python
sla = PerformanceSLA(
    cold_start_ms=500,
    warm_load_ms=50,
    cached_ms=5
)

config = load_env(performance_sla=sla)
# Warns if SLA breached
```

**Why**: **Predictable performance is important.** SLAs help identify performance issues early.

---

## Summary: Our Tradeoffs

| Decision | Tradeoff | Our Choice | Why |
|----------|----------|------------|-----|
| Precedence | Security vs Flexibility | Fixed, security-first | Production safety |
| Audit Trail | Performance vs Compliance | Per-variable audit | Compliance required |
| Cloud SDKs | Optional vs Required | Optional | CI/CD friendly |
| Failure Policies | Explicit vs Implicit | Explicit | Clarity |
| Caching | Performance vs Freshness | Caching with TTL | Performance matters |
| CI-Safe Mode | Validation vs Completeness | CI-safe validation | Security |
| Encrypted Configs | Security vs Complexity | Optional encryption | Flexibility |
| Backward Compatibility | Stability vs Clean API | Full compatibility | Adoption |
| Performance SLAs | Predictability vs Flexibility | SLAs with monitoring | Predictability |

**Philosophy**: **Security, predictability, and stability** over flexibility and API purity.
