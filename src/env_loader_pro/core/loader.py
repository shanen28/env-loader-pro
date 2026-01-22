"""Core loader with unified API for enterprise-grade configuration loading."""

import json
import os
import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple, Type, Union

from .audit import ConfigAudit
from .cache import Cache
from .merger import ConfigurationMerger
from .policy import PolicyManager, ProviderResult, create_default_policies
from .policy_code import Policy, load_policy
from .schema import SchemaValidator, extract_schema_info
from .tracing import Origin, Tracer
from ..crypto import get_decryptor_registry
from ..exceptions import EnvLoaderError, ValidationError
from ..providers.base import BaseProvider
from ..settings import DEFAULT_ENV_FILE
from ..utils.masking import is_secret_key, mask_value


def _expand_variables(value: str, env_dict: Dict[str, str], visited: Optional[set] = None) -> str:
    """Expand ${VAR} syntax with cycle detection."""
    if visited is None:
        visited = set()
    
    def replace_var(match):
        var_name = match.group(1)
        if var_name in visited:
            raise EnvLoaderError(f"Circular reference detected for variable: {var_name}")
        if var_name not in env_dict:
            return match.group(0)  # Return original if not found
        visited.add(var_name)
        result = _expand_variables(env_dict[var_name], env_dict, visited)
        visited.remove(var_name)
        return result
    
    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, value)


def _cast_value(value: str, to_type: Optional[Callable]) -> Any:
    """Cast a string value to the specified type."""
    if to_type is None:
        return value
    
    if to_type is bool:
        val = value.strip().lower()
        if val in ["1", "true", "yes", "y", "t"]:
            return True
        if val in ["0", "false", "no", "n", "f"]:
            return False
        raise EnvLoaderError(f"Cannot cast '{value}' to bool")
    
    # Handle list types
    try:
        if to_type == list or (isinstance(to_type, type) and to_type == list):
            # Try JSON first
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [item.strip() for item in value.split(',') if item.strip()]
    except (TypeError, AttributeError):
        pass
    
    try:
        return to_type(value)
    except Exception as e:
        raise EnvLoaderError(f"Failed to cast env value '{value}' to {to_type}: {e}")


def _parse_dotenv(
    path: str,
    expand_vars: bool = True,
    encrypted: bool = False,
    encryption_key: Optional[str] = None
) -> Dict[str, str]:
    """Parse .env file with optional encryption support."""
    out: Dict[str, str] = {}
    if not os.path.exists(path):
        return out
    
    # Handle encrypted files
    content = None
    if encrypted:
        try:
            registry = get_decryptor_registry()
            content = registry.decrypt(path, encryption_key)
        except Exception as e:
            raise EnvLoaderError(f"Failed to decrypt file {path}: {e}")
    
    if content is None:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
    
    # Parse content
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        out[key] = val
    
    # Expand variables if requested
    if expand_vars:
        expanded = {}
        for k, v in out.items():
            expanded[k] = _expand_variables(v, out)
        return expanded
    return out


def _load_from_providers(
    providers: List[BaseProvider],
    tracer: Optional[Tracer] = None,
    cache: Optional[Cache] = None,
    policy_manager: Optional[PolicyManager] = None,
    audit: Optional[ConfigAudit] = None,
) -> Dict[str, str]:
    """Load configuration from providers with policy-based error handling.
    
    Args:
        providers: List of provider instances
        tracer: Optional tracer for origin tracking
        cache: Optional cache for provider values
        policy_manager: Optional policy manager for error handling
        audit: Optional audit object for tracking
    
    Returns:
        Dictionary of provider values
    """
    result = {}
    policy_manager = policy_manager or PolicyManager()
    
    for provider in providers:
        provider_name = provider.__class__.__name__
        provider_result = None
        
        try:
            # Try get_all first (most efficient)
            if hasattr(provider, 'get_all') and callable(provider.get_all):
                provider_values = provider.get_all()
            else:
                # Fall back to get_many with empty list (providers should handle this)
                provider_values = provider.get_many([])
            
            # Apply caching if enabled
            if cache and cache.enabled:
                for key, value in provider_values.items():
                    cached = cache.get(f"provider:{provider_name}:{key}")
                    if cached is not None:
                        provider_values[key] = cached
                    else:
                        cache.set(f"provider:{provider_name}:{key}", value)
            
            provider_result = ProviderResult(data=provider_values)
            result.update(provider_values)
            
            # Record origins and audit
            if tracer and tracer.enabled:
                # Determine origin based on provider type
                if "Azure" in provider_name:
                    origin = Origin.CLOUD_AZURE
                elif "AWS" in provider_name:
                    origin = Origin.CLOUD_AWS
                elif "Docker" in provider_name:
                    origin = Origin.DOCKER
                elif "Kubernetes" in provider_name:
                    origin = Origin.K8S
                else:
                    origin = Origin.UNKNOWN
                
                for key in provider_values.keys():
                    tracer.record(key, origin, {"provider": provider_name})
                    if audit:
                        audit.add(
                            key=key,
                            source=origin.value,
                            provider=provider_name,
                            masked=is_secret_key(key),
                        )
        
        except Exception as e:
            # Handle error according to policy
            provider_result = ProviderResult(data={}, errors=[e])
            policy_manager.handle_error(provider_name, e)
            
            # Only continue if policy allows
            if not policy_manager.should_continue(provider_name):
                raise  # Re-raise if policy is FAIL
    
    return result


def load_env(
    env: Optional[str] = None,
    path: str = DEFAULT_ENV_FILE,
    strict: bool = False,
    trace: bool = False,
    audit: bool = False,
    providers: Optional[List[BaseProvider]] = None,
    cache: bool = True,
    cache_ttl: int = 3600,
    watch: bool = False,
    failure_policy: Optional[Dict[str, str]] = None,
    policy: Optional[Union[str, Policy]] = None,  # Policy-as-code
    # Legacy parameters (for backward compatibility)
    required: Optional[Iterable[str]] = None,
    optional: Optional[Iterable[str]] = None,
    types: Optional[Mapping[str, Callable]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    priority: str = "file",  # Legacy, not used in new architecture
    mask_secrets: bool = True,
    expand_vars: bool = True,
    rules: Optional[Mapping[str, Callable[[Any], bool]]] = None,
    schema: Optional[Union[Type, Any]] = None,
    nested: bool = False,
    nested_separator: str = "__",
    encrypted: bool = False,
    encryption_key: Optional[str] = None,
    # Advanced validation
    regex_validators: Optional[Mapping[str, str]] = None,
    deprecated_vars: Optional[List[str]] = None,
) -> Union[Dict[str, Any], Tuple[Dict[str, Any], ConfigAudit]]:
    """Load environment configuration with enterprise-grade features.
    
    This is the unified API for loading configuration from multiple sources
    with deterministic priority and full observability.
    
    Configuration Source Priority (highest to lowest):
    1. Cloud providers (Azure, AWS)
    2. System environment variables
    3. Docker/K8s mounted secrets
    4. .env.{env} (environment-specific)
    5. Base .env file
    6. Schema defaults
    
    Args:
        env: Environment name (e.g., 'prod', 'dev') - loads .env.{env}
        path: Path to base .env file
        strict: Enable strict mode (fail on unknown variables)
        trace: Enable origin tracking for observability
        audit: Enable audit tracking (returns tuple: (config, audit))
        providers: List of BaseProvider instances (Azure, AWS, etc.)
        cache: Enable caching for provider values
        cache_ttl: Cache TTL in seconds
        watch: Enable live reloading (requires watchdog)
        failure_policy: Dictionary mapping provider names to policies (fail/warn/fallback)
        policy: Policy file path or Policy instance for policy-as-code enforcement
        required: Required variable names (legacy)
        optional: Optional variable names (legacy, for documentation)
        types: Type mapping for variables (legacy)
        defaults: Default values (legacy)
        priority: Legacy parameter (not used, kept for compatibility)
        mask_secrets: Mask secrets in safe_repr() (default: True)
        expand_vars: Enable ${VAR} expansion (default: True)
        rules: Custom validation rules (legacy)
        schema: Pydantic model or dataclass (legacy, use load_with_schema instead)
        nested: Convert flat keys to nested structure (legacy)
        nested_separator: Separator for nested keys (legacy)
        encrypted: Enable encrypted .env file support
        encryption_key: Encryption key or path to key file
        regex_validators: Regex patterns for validation
        deprecated_vars: List of deprecated variable names
    
    Returns:
        ConfigDict with loaded configuration and metadata methods.
        If audit=True, returns tuple (config, audit).
    
    Raises:
        EnvLoaderError: On configuration errors
        ValidationError: On validation failures
    """
    # Initialize components
    tracer = Tracer(enabled=trace, mask_secrets=mask_secrets)
    cache_obj = Cache(ttl=cache_ttl, enabled=cache)
    merger = ConfigurationMerger(tracer=tracer)
    audit_obj = ConfigAudit() if audit else None
    
    # Initialize policy manager
    if failure_policy:
        policy_manager = PolicyManager(policies=failure_policy)
    else:
        policy_manager = PolicyManager(policies=create_default_policies())
    
    # Load policy-as-code if provided
    config_policy = None
    if policy:
        if isinstance(policy, str):
            config_policy = load_policy(policy)
        elif isinstance(policy, Policy):
            config_policy = policy
    
    # Normalize inputs
    required = set(required or [])
    optional = set(optional or [])
    types = dict(types or {})
    defaults = dict(defaults or {})
    rules = dict(rules or {})
    providers = providers or []
    
    # Extract schema info if provided
    schema_info = None
    if schema:
        schema_info = extract_schema_info(schema)
        # Merge schema info with provided parameters
        required.update(schema_info.get("required", []))
        optional.update(schema_info.get("optional", []))
        types.update(schema_info.get("types", {}))
        defaults.update(schema_info.get("defaults", {}))
    
    # Build sources dictionary
    sources = {}
    
    # 1. Schema defaults (lowest priority)
    if defaults:
        sources["schema_defaults"] = {k: str(v) for k, v in defaults.items()}
        if tracer.enabled:
            for key in defaults.keys():
                tracer.record(key, Origin.SCHEMA_DEFAULT)
        if audit_obj:
            for key in defaults.keys():
                audit_obj.add(
                    key=key,
                    source=Origin.SCHEMA_DEFAULT.value,
                    masked=is_secret_key(key),
                )
    
    # 2. Base .env file
    if os.path.exists(path):
        base_vars = _parse_dotenv(path, expand_vars=expand_vars, encrypted=encrypted, encryption_key=encryption_key)
        sources["base_file"] = base_vars
        if tracer.enabled:
            for key in base_vars.keys():
                tracer.record(key, Origin.FILE_BASE)
        if audit_obj:
            for key in base_vars.keys():
                audit_obj.add(
                    key=key,
                    source=Origin.FILE_BASE.value,
                    masked=is_secret_key(key),
                )
    
    # 3. Environment-specific .env.{env}
    if env:
        base_dir = os.path.dirname(path) or "."
        env_file = os.path.join(base_dir, f".env.{env}")
        if os.path.exists(env_file):
            env_vars = _parse_dotenv(env_file, expand_vars=expand_vars, encrypted=encrypted, encryption_key=encryption_key)
            sources["env_specific"] = env_vars
            if tracer.enabled:
                for key in env_vars.keys():
                    tracer.record(key, Origin.FILE_ENV_SPECIFIC)
            if audit_obj:
                for key in env_vars.keys():
                    audit_obj.add(
                        key=key,
                        source=Origin.FILE_ENV_SPECIFIC.value,
                        masked=is_secret_key(key),
                    )
    
    # 4. Docker/K8s mounted secrets
    # Auto-detect and load if available
    try:
        from ..providers.docker import DockerSecretsProvider, KubernetesSecretsProvider
        
        docker_provider = DockerSecretsProvider()
        k8s_provider = KubernetesSecretsProvider()
        
        docker_vars = {}
        k8s_vars = {}
        
        if docker_provider.is_available():
            docker_vars = docker_provider.get_all()
        
        if k8s_provider.is_available():
            k8s_vars = k8s_provider.get_all()
        
        if docker_vars or k8s_vars:
            sources["docker_k8s"] = {**docker_vars, **k8s_vars}
            if tracer.enabled:
                for key in docker_vars.keys():
                    tracer.record(key, Origin.DOCKER)
                for key in k8s_vars.keys():
                    tracer.record(key, Origin.K8S)
            if audit_obj:
                for key in docker_vars.keys():
                    audit_obj.add(
                        key=key,
                        source=Origin.DOCKER.value,
                        provider="DockerSecretsProvider",
                        masked=is_secret_key(key),
                    )
                for key in k8s_vars.keys():
                    audit_obj.add(
                        key=key,
                        source=Origin.K8S.value,
                        provider="KubernetesSecretsProvider",
                        masked=is_secret_key(key),
                    )
    except ImportError:
        pass
    
    # 5. System environment variables
    system_vars = dict(os.environ)
    sources["system"] = system_vars
    if tracer.enabled:
        for key in system_vars.keys():
            if key not in [k for s in sources.values() for k in s.keys()]:
                tracer.record(key, Origin.SYSTEM)
    if audit_obj:
        for key in system_vars.keys():
            if key not in audit_obj.entries:
                audit_obj.add(
                    key=key,
                    source=Origin.SYSTEM.value,
                    masked=is_secret_key(key),
                )
    
    # 6. Cloud providers (highest priority)
    provider_vars = _load_from_providers(
        providers,
        tracer=tracer,
        cache=cache_obj,
        policy_manager=policy_manager,
        audit=audit_obj,
    )
    if provider_vars:
        sources["cloud_providers"] = provider_vars
    
    # Merge all sources with deterministic priority
    merged = merger.merge(sources)
    
    # Re-expand variables after merging (in case system vars are referenced)
    if expand_vars:
        for k, v in list(merged.items()):
            if isinstance(v, str) and '${' in v:
                merged[k] = _expand_variables(v, merged)
    
    # Apply defaults for missing keys
    for k, v in defaults.items():
        merged.setdefault(k, str(v))
    
    # Type casting
    parsed: Dict[str, Any] = {}
    for k, v in merged.items():
        cast_to = types.get(k)
        try:
            parsed[k] = _cast_value(v, cast_to)
        except EnvLoaderError:
            raise
    
    # Replace stringified defaults with original types
    for k, d in defaults.items():
        if k in parsed:
            if isinstance(parsed[k], str) and str(d) == parsed[k] and not types.get(k):
                parsed[k] = d
        else:
            parsed[k] = d
    
    # Validation
    known_vars = required | optional | set(types.keys()) | set(defaults.keys())
    
    # Build regex validators
    compiled_regex = {}
    if regex_validators:
        for key, pattern in regex_validators.items():
            compiled_regex[key] = re.compile(pattern)
    
    validator = SchemaValidator(
        strict=strict,
        custom_validators=rules,
        regex_validators=compiled_regex,
        deprecated_vars=deprecated_vars,
    )
    
    validator.validate(parsed, known_vars=list(known_vars), required_vars=list(required))
    
    # Apply policy-as-code if provided
    if config_policy:
        config_policy.validate(parsed, audit=audit_obj)
    
    # Create ConfigDict with metadata methods
    class ConfigDict(dict):
        """Configuration dictionary with metadata methods."""
        
        def safe_repr(self) -> Dict[str, Any]:
            """Get safe representation with masked secrets."""
            from ..utils.masking import mask_dict
            return mask_dict(self, custom_secrets=None)
        
        def save(self, filepath: str, format: str = "json") -> None:
            """Save config to file."""
            if format.lower() == "json":
                with open(filepath, "w") as f:
                    json.dump(self.safe_repr(), f, indent=2)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    with open(filepath, "w") as f:
                        yaml.dump(self.safe_repr(), f, default_flow_style=False)
                except ImportError:
                    raise EnvLoaderError("PyYAML required for YAML export. Install: pip install pyyaml")
            else:
                raise EnvLoaderError(f"Unsupported format: {format}. Use 'json' or 'yaml'")
        
        def get_origins(self) -> Dict[str, str]:
            """Get variable origins (if tracing enabled)."""
            return tracer.get_all_origins() if trace else {}
        
        def trace(self, key: str) -> str:
            """Get origin of a specific variable."""
            if trace:
                origin = tracer.get_origin(key)
                return origin.value if origin else "unknown"
            return "tracing_disabled"
    
    result = ConfigDict(parsed)
    
    # Print trace if enabled
    if trace:
        tracer.print_trace(parsed)
    
    # Return with audit if requested
    if audit and audit_obj:
        return result, audit_obj
    
    return result
