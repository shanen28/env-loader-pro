import os
import re
import json
import warnings
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Union, Type
from pathlib import Path
from collections import defaultdict

class EnvLoaderError(Exception):
    pass

_DEFAULT_SECRET_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r".*secret.*",
    r".*key.*",
    r".*token.*",
    r".*password.*",
    r".*pwd.*",
]]

def _is_secret(key: str) -> bool:
    return any(p.match(key) for p in _DEFAULT_SECRET_PATTERNS)

def _mask(value: Any) -> str:
    if value is None:
        return "None"
    s = str(value)
    if len(s) <= 4:
        return "*" * len(s)
    return "*" * (len(s) - 4) + s[-4:]

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

def _parse_dotenv(path: str, expand_vars: bool = True, encrypted: bool = False, encryption_key: Optional[str] = None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not os.path.exists(path):
        return out
    
    # Handle encrypted files
    content = None
    if encrypted:
        try:
            content = _decrypt_file(path, encryption_key)
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

def _decrypt_file(path: str, key: Optional[str] = None) -> str:
    """Decrypt an encrypted .env file.
    
    Supports multiple encryption methods:
    - age encryption
    - GPG encryption
    - openssl encryption
    
    Args:
        path: Path to encrypted file
        key: Decryption key or path to key file
    
    Returns:
        Decrypted file content
    """
    # Try age first
    try:
        import subprocess
        if key:
            result = subprocess.run(
                ["age", "--decrypt", "-i", key, path],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            result = subprocess.run(
                ["age", "--decrypt", path],
                capture_output=True,
                text=True,
                check=True
            )
        return result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Try GPG
    try:
        import subprocess
        cmd = ["gpg", "--decrypt", path]
        if key:
            cmd.extend(["--passphrase", key])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Try openssl
    try:
        import subprocess
        if not key:
            raise EnvLoaderError("Encryption key required for openssl decryption")
        
        result = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-salt", "-in", path, "-pass", f"pass:{key}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    raise EnvLoaderError(
        "No decryption tool available. Install age, gpg, or openssl, "
        "or provide decrypted file content."
    )

def _merge_envs(primary: Mapping[str, str], secondary: Mapping[str, str]) -> Dict[str, str]:
    # primary wins
    merged = dict(secondary)
    merged.update(primary)
    return merged

def _nest_config(flat_config: Dict[str, Any], separator: str = "__") -> Dict[str, Any]:
    """Convert flat config with DB__HOST syntax to nested structure.
    
    Example:
        {"DB__HOST": "localhost", "DB__PORT": 5432}
        -> {"DB": {"HOST": "localhost", "PORT": 5432}}
    
    Args:
        flat_config: Flat dictionary with nested keys
        separator: Separator used in nested keys (default: "__")
    
    Returns:
        Nested dictionary structure
    """
    nested = {}
    
    for key, value in flat_config.items():
        if separator in key:
            parts = key.split(separator, 1)  # Split only on first occurrence
            prefix = parts[0]
            suffix = parts[1]
            
            if prefix not in nested:
                nested[prefix] = {}
            
            # Recursively handle deeper nesting
            if separator in suffix:
                nested[prefix].update(_nest_config({suffix: value}, separator))
            else:
                nested[prefix][suffix] = value
        else:
            nested[key] = value
    
    return nested

def _flatten_nested_config(nested_config: Dict[str, Any], separator: str = "__", parent: str = "") -> Dict[str, Any]:
    """Convert nested config to flat structure.
    
    Example:
        {"DB": {"HOST": "localhost", "PORT": 5432}}
        -> {"DB__HOST": "localhost", "DB__PORT": 5432}
    
    Args:
        nested_config: Nested dictionary
        separator: Separator to use (default: "__")
        parent: Parent key prefix
    
    Returns:
        Flat dictionary
    """
    flat = {}
    
    for key, value in nested_config.items():
        full_key = f"{parent}{separator}{key}" if parent else key
        
        if isinstance(value, dict):
            flat.update(_flatten_nested_config(value, separator, full_key))
        else:
            flat[full_key] = value
    
    return flat

def _find_env_file(base_path: str, env: Optional[str] = None) -> str:
    """Find the appropriate .env file based on environment name."""
    if env:
        env_file = f".env.{env}"
        if os.path.exists(env_file):
            return env_file
    # Fall back to .env
    if os.path.exists(base_path):
        return base_path
    return base_path

def load_env(
    path: str = ".env",
    env: Optional[str] = None,
    required: Optional[Iterable[str]] = None,
    optional: Optional[Iterable[str]] = None,
    types: Optional[Mapping[str, Callable]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    priority: str = "file",  # 'file' or 'system' (system overrides file when 'system')
    mask_secrets: bool = True,
    expand_vars: bool = True,
    rules: Optional[Mapping[str, Callable[[Any], bool]]] = None,
    strict: bool = False,
    schema: Optional[Union[Type, Any]] = None,
    providers: Optional[List[Any]] = None,  # List of BaseProvider instances
    nested: bool = False,  # Enable nested config (DB__HOST -> DB.HOST)
    nested_separator: str = "__",  # Separator for nested keys
    encrypted: bool = False,  # Enable encrypted .env file support
    encryption_key: Optional[str] = None,  # Encryption key or path
    watch: bool = False,  # Enable file watching/reloading
    trace: bool = False,  # Enable tracing of variable origins
) -> Dict[str, Any]:
    """Load environment configuration.

    Args:
        path: path to .env file (if absent, treated as empty)
        env: environment name (e.g., 'dev', 'prod') - loads .env.{env} if exists
        required: iterable of required variable names
        optional: iterable of optional variable names (for documentation)
        types: mapping of var name -> type callable (e.g., int, bool, list)
        defaults: mapping of default values
        priority: either 'file' (file overrides system) or 'system' (system overrides file)
        mask_secrets: whether to mask secrets when printing
        expand_vars: whether to expand ${VAR} syntax
        rules: mapping of var name -> validation function (returns bool)
        strict: if True, warn about unknown variables not in required/optional/types
        schema: Pydantic model or dataclass class for schema validation
        providers: list of BaseProvider instances (Azure, AWS, Docker, etc.)
        nested: if True, convert flat keys with separator to nested structure
        nested_separator: separator for nested keys (default: "__")
        encrypted: if True, decrypt .env file using encryption_key
        encryption_key: encryption key or path to key file
        watch: if True, watch for file changes and reload (requires watchdog)
        trace: if True, track variable origins for observability

    Returns:
        dict of variable name -> typed value (with save() and safe_repr() methods)

    Raises:
        EnvLoaderError on missing required variables or invalid casts
    """
    required = set(required or [])
    optional = set(optional or [])
    types = dict(types or {})
    defaults = dict(defaults or {})
    rules = dict(rules or {})
    providers = providers or []
    
    # Variable origin tracking for observability
    variable_origins: Dict[str, str] = {}
    
    # Find the right env file
    actual_path = _find_env_file(path, env)
    
    # Load from multiple sources if env is specified
    dotenv_vars = {}
    if env:
        # First load base .env if it exists
        if os.path.exists(path):
            parsed = _parse_dotenv(path, expand_vars=expand_vars, encrypted=encrypted, encryption_key=encryption_key)
            dotenv_vars = parsed
            if trace:
                for k in parsed:
                    variable_origins[k] = "file"
        # Then load .env.{env} and merge (env-specific overrides base)
        # Construct path in same directory as base .env file
        base_dir = os.path.dirname(path) or "."
        env_file = os.path.join(base_dir, f".env.{env}")
        if os.path.exists(env_file):
            env_vars = _parse_dotenv(env_file, expand_vars=expand_vars, encrypted=encrypted, encryption_key=encryption_key)
            dotenv_vars = _merge_envs(env_vars, dotenv_vars)  # env-specific wins
            if trace:
                for k in env_vars:
                    variable_origins[k] = f"file.{env}"
    else:
        parsed = _parse_dotenv(actual_path, expand_vars=expand_vars, encrypted=encrypted, encryption_key=encryption_key)
        dotenv_vars = parsed
        if trace:
            for k in parsed:
                variable_origins[k] = "file"
    
    system_vars = dict(os.environ)
    if trace:
        for k in system_vars:
            if k not in variable_origins:
                variable_origins[k] = "system"
    
    # Merge sources in priority order (lower priority first, higher priority overrides)
    # Priority order: defaults < base .env < env-specific .env < system < providers
    raw = {}
    
    # 1. Start with defaults
    raw.update({k: str(v) for k, v in defaults.items()})
    
    # 2. Add base .env file
    if priority == "file":
        raw = _merge_envs(dotenv_vars, raw)
    else:
        raw = _merge_envs(raw, dotenv_vars)
    
    # 3. Add system environment
    if priority == "system":
        raw = _merge_envs(system_vars, raw)
    else:
        raw = _merge_envs(raw, system_vars)
    
    # 4. Load from providers (highest priority)
    provider_vars = {}
    for provider in providers:
        try:
            if hasattr(provider, 'get_all') and callable(provider.get_all):
                # Provider supports getting all values
                provider_values = provider.get_all()
            else:
                # Provider only supports get/get_many
                # Get all keys we're interested in
                all_keys = set(raw.keys()) | required
                provider_values = provider.get_many(list(all_keys))
            
            provider_vars.update(provider_values)
            if trace:
                provider_name = provider.__class__.__name__
                for k in provider_values:
                    variable_origins[k] = f"provider.{provider_name}"
        except Exception as e:
            if strict:
                warnings.warn(f"Provider {provider.__class__.__name__} failed: {e}", UserWarning)
    
    # Merge provider values (providers have highest priority)
    raw = _merge_envs(provider_vars, raw)
    
    # Re-expand after merging (in case system vars are referenced)
    if expand_vars:
        for k, v in list(raw.items()):
            if isinstance(v, str) and '${' in v:
                raw[k] = _expand_variables(v, raw)
    
    # apply defaults for keys not present
    for k, v in defaults.items():
        raw.setdefault(k, str(v))
    
    # Strict mode: check for unknown variables
    if strict:
        known_vars = required | optional | set(types.keys()) | set(defaults.keys())
        unknown_vars = set(raw.keys()) - known_vars
        if unknown_vars:
            warnings.warn(
                f"Unknown environment variables found (strict mode): {', '.join(sorted(unknown_vars))}",
                UserWarning
            )
    
    missing = [k for k in required if k not in raw or raw.get(k) == ""]
    if missing:
        raise EnvLoaderError(f"Missing required environment variables: {', '.join(missing)}")
    
    parsed: Dict[str, Any] = {}
    
    for k, v in raw.items():
        cast_to = types.get(k)
        try:
            parsed[k] = _cast_value(v, cast_to)
        except EnvLoaderError:
            # add context and re-raise
            raise
    
    # For convenience return typed values with defaults applied as their Python types
    # If a key from defaults was set from the stringified default, replace it with the original
    # This preserves the original type of the default value
    for k, d in defaults.items():
        # Check if this key was set from our default (stringified version)
        # If the parsed value is a string that matches the stringified default, replace it
        if k in parsed:
            # If the value is the string version of our default, replace with original
            if isinstance(parsed[k], str) and str(d) == parsed[k] and not types.get(k):
                parsed[k] = d
        else:
            # Key not in parsed, use original default
            parsed[k] = d
    
    # Convert to nested structure if requested
    if nested:
        parsed = _nest_config(parsed, nested_separator)
    
    # Apply validation rules (on flat keys before nesting or on nested structure)
    validation_keys = _flatten_nested_config(parsed, nested_separator) if nested else parsed
    for k, rule_func in rules.items():
        # Handle nested keys in validation
        flat_k = k.replace(".", nested_separator) if nested else k
        if flat_k in validation_keys:
            value = validation_keys[flat_k]
            if not rule_func(value):
                raise EnvLoaderError(f"Validation rule failed for '{k}': {value}")
    
    # Schema validation (Pydantic or dataclass)
    # Note: When schema is used via load_with_schema(), schema=None is passed
    # and the schema conversion happens in schema.py. Here we only handle
    # direct schema usage in load_env().
    if schema:
        schema_result = _apply_schema(parsed, schema)
        # _apply_schema may return a dict or a schema instance
        if isinstance(schema_result, dict):
            parsed = schema_result
        else:
            # Schema instance returned - convert to dict for ConfigDict
            try:
                # Try Pydantic .dict() method
                if hasattr(schema_result, 'dict'):
                    parsed = schema_result.dict()
                # Try dataclass asdict
                elif hasattr(schema_result, '__dataclass_fields__'):
                    from dataclasses import asdict
                    parsed = asdict(schema_result)
                else:
                    # Fallback: keep original parsed
                    pass
            except Exception:
                # If conversion fails, keep original parsed
                pass
    
    # attach a safe repr function
    def safe_repr(mapping: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        for kk, vv in mapping.items():
            if mask_secrets and _is_secret(kk):
                out[kk] = _mask(vv)
            else:
                out[kk] = vv
        return out
    
    # attach save function
    def save_config(filepath: str, format: str = "json") -> None:
        """Save config to JSON or YAML file."""
        if format.lower() == "json":
            with open(filepath, "w") as f:
                json.dump(safe_repr(parsed), f, indent=2)
        elif format.lower() == "yaml":
            try:
                import yaml
                with open(filepath, "w") as f:
                    yaml.dump(safe_repr(parsed), f, default_flow_style=False)
            except ImportError:
                raise EnvLoaderError("PyYAML is required for YAML export. Install with: pip install pyyaml")
        else:
            raise EnvLoaderError(f"Unsupported format: {format}. Use 'json' or 'yaml'")
    
    # Create a custom dict subclass to attach methods
    class ConfigDict(dict):
        def safe_repr(self):
            return safe_repr(self)
        
        def save(self, filepath: str, format: str = "json"):
            return save_config(filepath, format)
        
        def get_origins(self) -> Dict[str, str]:
            """Get variable origins for observability."""
            return variable_origins.copy() if trace else {}
        
        def trace(self, key: str) -> str:
            """Get origin of a specific variable."""
            if trace:
                return variable_origins.get(key, "unknown")
            return "tracing_disabled"

    result = ConfigDict(parsed)
    
    # Print trace information if requested
    if trace:
        print("=== Configuration Trace ===")
        for key, origin in sorted(variable_origins.items()):
            if key in parsed:
                print(f"{key}: {origin}")
    
    return result

def _apply_schema(parsed: Dict[str, Any], schema: Union[Type, Any]) -> Dict[str, Any]:
    """Apply schema validation using Pydantic or dataclass."""
    # Try Pydantic first
    try:
        from pydantic import BaseModel
        if issubclass(schema, BaseModel):
            # Normalize keys for Pydantic (case-insensitive)
            field_names = set(schema.__fields__.keys())
            normalized = {}
            for k, v in parsed.items():
                for field_name in field_names:
                    if k.upper() == field_name.upper():
                        normalized[field_name] = v
                        break
            
            instance = schema(**normalized)
            # Return the instance itself, not a dict
            return instance
    except ImportError:
        pass
    except Exception:
        # Not a Pydantic model, try dataclass
        pass
    
    # Try dataclass
    try:
        from dataclasses import fields
        if hasattr(schema, '__dataclass_fields__'):
            field_names = {f.name for f in fields(schema)}
            # Filter to only schema fields (case-insensitive matching)
            filtered = {}
            for k, v in parsed.items():
                # Find matching field name (case-insensitive)
                for field_name in field_names:
                    if k.upper() == field_name.upper():
                        filtered[field_name] = v
                        break
            
            instance = schema(**filtered)
            # Return the instance itself, not a dict
            return instance
    except Exception as e:
        # If instantiation fails, return parsed as-is
        pass
    
    # If neither works, return as-is but warn
    warnings.warn(f"Schema {schema} is not a recognized Pydantic model or dataclass", UserWarning)
    return parsed

def generate_env_example(
    required: Optional[Iterable[str]] = None,
    optional: Optional[Iterable[str]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    types: Optional[Mapping[str, Callable]] = None,
    output_path: str = ".env.example",
) -> None:
    """Generate a .env.example file from schema."""
    lines = []
    lines.append("# Environment Configuration")
    lines.append("# Copy this file to .env and fill in your values")
    lines.append("")
    
    all_vars = set(required or []) | set(optional or []) | set(defaults.keys()) | set(types.keys())
    
    if required:
        lines.append("# Required variables")
        for var in sorted(required):
            default_val = defaults.get(var, "")
            type_hint = types.get(var, str)
            comment = f"  # {type_hint.__name__}"
            lines.append(f"{var}={default_val}{comment}")
        lines.append("")
    
    if optional:
        lines.append("# Optional variables")
        for var in sorted(optional):
            if var not in required:
                default_val = defaults.get(var, "")
                type_hint = types.get(var, str)
                comment = f"  # {type_hint.__name__}"
                lines.append(f"{var}={default_val}{comment}")
        lines.append("")
    
    # Other variables from defaults/types
    other_vars = (set(defaults.keys()) | set(types.keys())) - set(required or []) - set(optional or [])
    if other_vars:
        lines.append("# Additional variables")
        for var in sorted(other_vars):
            default_val = defaults.get(var, "")
            type_hint = types.get(var, str)
            comment = f"  # {type_hint.__name__}"
            lines.append(f"{var}={default_val}{comment}")
    
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
