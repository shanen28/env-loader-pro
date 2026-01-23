# load_env

Main function for loading environment configuration.

## Signature

```python
def load_env(
    env: Optional[str] = None,
    path: str = ".env",
    strict: bool = False,
    trace: bool = False,
    providers: Optional[List[BaseProvider]] = None,
    cache: bool = True,
    cache_ttl: int = 3600,
    watch: bool = False,
    audit: bool = False,
    failure_policy: Optional[Dict[str, Union[str, FailurePolicy]]] = None,
    performance_sla: Optional[PerformanceSLA] = None,
    policy_file: Optional[str] = None,
    required: Optional[List[str]] = None,
    types: Optional[Dict[str, Type]] = None,
    defaults: Optional[Dict[str, Any]] = None,
    rules: Optional[Dict[str, Callable]] = None,
    priority: str = "system",
    encrypted: bool = False,
    encryption_key: Optional[str] = None,
) -> Union[ConfigDict, Tuple[ConfigDict, ConfigAudit]]:
```

## Parameters

- `env` - Environment name (e.g., "prod", "dev")
- `path` - Path to .env file
- `strict` - Enable strict mode
- `trace` - Enable origin tracking
- `providers` - List of configuration providers
- `cache` - Enable caching
- `cache_ttl` - Cache TTL in seconds
- `watch` - Enable file watching
- `audit` - Enable audit trail
- `failure_policy` - Per-provider failure policies
- `performance_sla` - Performance SLA
- `policy_file` - Policy-as-code file path
- `required` - Required variables
- `types` - Type casting
- `defaults` - Default values
- `rules` - Validation rules
- `priority` - Priority mode
- `encrypted` - Load encrypted file
- `encryption_key` - Encryption key path

## Returns

- `ConfigDict` - Configuration dictionary
- `Tuple[ConfigDict, ConfigAudit]` - If `audit=True`

## Examples

### Basic

```python
config = load_env()
```

### With Types

```python
config = load_env(types={"PORT": int, "DEBUG": bool})
```

### With Audit

```python
config, audit = load_env(audit=True)
```

## Related Topics

- [Getting Started](../getting-started/quickstart.md)
- [Core Concepts](../core-concepts/precedence.md)
