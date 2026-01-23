# load_with_schema

Load configuration with Pydantic or dataclass schema validation.

## Signature

```python
def load_with_schema(
    schema: Union[Type[BaseModel], Type],
    env: Optional[str] = None,
    path: str = ".env",
    strict: bool = False,
    trace: bool = False,
    providers: Optional[List[BaseProvider]] = None,
    cache: bool = True,
    cache_ttl: int = 3600,
    audit: bool = False,
    failure_policy: Optional[Dict[str, Union[str, FailurePolicy]]] = None,
    policy_file: Optional[str] = None,
) -> Union[BaseModel, Any]:
```

## Parameters

- `schema` - Pydantic model or dataclass
- `env` - Environment name
- `path` - Path to .env file
- `strict` - Enable strict mode
- `trace` - Enable origin tracking
- `providers` - List of providers
- `cache` - Enable caching
- `cache_ttl` - Cache TTL
- `audit` - Enable audit trail
- `failure_policy` - Failure policies
- `policy_file` - Policy file

## Returns

- Schema instance with loaded values

## Examples

### Pydantic

```python
from pydantic import BaseModel

class Config(BaseModel):
    port: int = 8080
    debug: bool = False
    api_key: str

config = load_with_schema(Config)
```

### Dataclass

```python
from dataclasses import dataclass

@dataclass
class Config:
    port: int = 8080
    debug: bool = False
    api_key: str

config = load_with_schema(Config)
```

## Related Topics

- [Schema Support](../core-concepts/schema.md)
