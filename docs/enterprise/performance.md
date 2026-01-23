# Performance

Performance monitoring, SLAs, and optimization.

## Performance SLAs

env-loader-pro maintains performance guarantees:

- **Cold start**: < 500ms
- **Warm load**: < 50ms
- **Cached**: < 5ms

## Performance Monitoring

### Enable Monitoring

```python
from env_loader_pro import load_env, PerformanceSLA

# Define SLA
sla = PerformanceSLA(
    cold_start_ms=500,
    warm_load_ms=50,
    cached_ms=5
)

# Load with monitoring
config = load_env(
    env="prod",
    performance_sla=sla,
    trace=True
)

# Access metrics
metrics = config.performance_metrics
print(f"Total load time: {metrics.total_load_time_ms}ms")
print(f"Source times: {metrics.source_load_times_ms}")
```

## Caching

### Enable Caching

```python
config = load_env(
    env="prod",
    cache=True,
    cache_ttl=3600  # 1 hour
)
```

### Provider Caching

```python
from env_loader_pro.providers import AzureKeyVaultProvider

provider = AzureKeyVaultProvider(
    vault_url="...",
    cache=True,
    cache_ttl=3600
)

config = load_env(providers=[provider])
```

## Circuit Breaker

Prevent cascading failures:

```python
from env_loader_pro.core import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    timeout_seconds=60
)

if breaker.should_attempt():
    try:
        value = provider.get("KEY")
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
```

## Performance Best Practices

1. **Enable caching** for cloud providers
2. **Set appropriate TTL** based on secret rotation
3. **Use circuit breakers** for resilience
4. **Monitor performance** in production
5. **Optimize provider calls** with batch operations

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Caching](../core-concepts/precedence.md)
