"""Enhanced schema validation with strict mode and advanced validation."""

import re
import warnings
from typing import Any, Callable, Dict, List, Optional, Pattern, Type, Union

from ..exceptions import SchemaError, ValidationError


class SchemaValidator:
    """Validates configuration against schema with strict mode support."""
    
    def __init__(
        self,
        strict: bool = False,
        warn_only: bool = True,
        custom_validators: Optional[Dict[str, Callable]] = None,
        regex_validators: Optional[Dict[str, Pattern]] = None,
        deprecated_vars: Optional[List[str]] = None,
    ):
        """Initialize schema validator.
        
        Args:
            strict: Enable strict mode (fail on unknown variables)
            warn_only: In strict mode, warn instead of fail
            custom_validators: Custom validation functions per key
            regex_validators: Regex patterns for validation per key
            deprecated_vars: List of deprecated variable names
        """
        self.strict = strict
        self.warn_only = warn_only
        self.custom_validators = custom_validators or {}
        self.regex_validators = regex_validators or {}
        self.deprecated_vars = set(deprecated_vars or [])
    
    def validate(
        self,
        config: Dict[str, Any],
        known_vars: Optional[List[str]] = None,
        required_vars: Optional[List[str]] = None,
    ) -> None:
        """Validate configuration.
        
        Args:
            config: Configuration dictionary
            known_vars: List of known/expected variable names
            required_vars: List of required variable names
        
        Raises:
            ValidationError: If validation fails
            SchemaError: If strict mode violations occur
        """
        known_vars = set(known_vars or [])
        required_vars = set(required_vars or [])
        
        # Check required variables
        missing = required_vars - set(config.keys())
        if missing:
            raise ValidationError(
                f"Missing required variables: {', '.join(sorted(missing))}"
            )
        
        # Check for empty required values
        for var in required_vars:
            if var in config and (config[var] is None or config[var] == ""):
                raise ValidationError(f"Required variable '{var}' is empty")
        
        # Strict mode: check for unknown variables
        if self.strict:
            unknown = set(config.keys()) - known_vars - required_vars
            if unknown:
                msg = f"Unknown variables found: {', '.join(sorted(unknown))}"
                if self.warn_only:
                    warnings.warn(msg, UserWarning)
                else:
                    raise SchemaError(msg)
        
        # Check deprecated variables
        deprecated_found = self.deprecated_vars & set(config.keys())
        if deprecated_found:
            for var in deprecated_found:
                warnings.warn(
                    f"Variable '{var}' is deprecated and will be removed in a future version",
                    DeprecationWarning
                )
        
        # Apply custom validators
        for key, validator in self.custom_validators.items():
            if key in config:
                try:
                    if not validator(config[key]):
                        raise ValidationError(
                            f"Custom validation failed for '{key}': {config[key]}"
                        )
                except Exception as e:
                    if isinstance(e, ValidationError):
                        raise
                    raise ValidationError(
                        f"Validation error for '{key}': {str(e)}"
                    )
        
        # Apply regex validators
        for key, pattern in self.regex_validators.items():
            if key in config:
                value = str(config[key])
                if not pattern.match(value):
                    raise ValidationError(
                        f"Regex validation failed for '{key}': value '{value}' "
                        f"does not match pattern '{pattern.pattern}'"
                    )
    
    def validate_type(self, key: str, value: Any, expected_type: Type) -> None:
        """Validate that a value matches expected type.
        
        Args:
            key: Variable key name
            value: Value to validate
            expected_type: Expected type
        
        Raises:
            ValidationError: If type doesn't match
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Variable '{key}' has type {type(value).__name__}, "
                f"expected {expected_type.__name__}"
            )


def extract_schema_info(
    schema: Union[Type, Any]
) -> Dict[str, Any]:
    """Extract validation information from schema.
    
    Args:
        schema: Pydantic model or dataclass
    
    Returns:
        Dictionary with extracted schema information
    """
    field_names = _get_schema_fields(schema)
    field_types = _get_field_types(schema)
    field_defaults = _get_field_defaults(schema)
    
    # Map to uppercase for env vars
    types_mapping = {}
    defaults_mapping = {}
    required_vars = []
    optional_vars = []
    
    for field_name in field_names:
        upper_name = field_name.upper()
        types_mapping[upper_name] = field_types.get(field_name, str)
        
        if field_name in field_defaults:
            defaults_mapping[upper_name] = field_defaults[field_name]
        
        if _is_required_field(schema, field_name):
            required_vars.append(upper_name)
        else:
            optional_vars.append(upper_name)
    
    return {
        "field_names": field_names,
        "types": types_mapping,
        "defaults": defaults_mapping,
        "required": required_vars,
        "optional": optional_vars,
    }


def _get_schema_fields(schema: Union[Type, Any]) -> List[str]:
    """Extract field names from schema."""
    # Try Pydantic
    try:
        from pydantic import BaseModel
        if issubclass(schema, BaseModel):
            return list(schema.__fields__.keys())
    except (ImportError, TypeError):
        pass
    
    # Try dataclass
    try:
        from dataclasses import fields
        if hasattr(schema, '__dataclass_fields__'):
            return [f.name for f in fields(schema)]
    except Exception:
        pass
    
    return []


def _is_required_field(schema: Union[Type, Any], field_name: str) -> bool:
    """Check if a field is required."""
    # Try Pydantic
    try:
        from pydantic import BaseModel
        if issubclass(schema, BaseModel):
            field = schema.__fields__.get(field_name)
            if field:
                return field.required
    except (ImportError, TypeError):
        pass
    
    # Try dataclass
    try:
        from dataclasses import fields, MISSING
        if hasattr(schema, '__dataclass_fields__'):
            for f in fields(schema):
                if f.name == field_name:
                    return f.default == MISSING and f.default_factory == MISSING
    except Exception:
        pass
    
    return True


def _get_field_types(schema: Union[Type, Any]) -> Dict[str, type]:
    """Extract type hints from schema."""
    types = {}
    
    # Try Pydantic
    try:
        from pydantic import BaseModel
        if issubclass(schema, BaseModel):
            for name, field in schema.__fields__.items():
                types[name] = field.outer_type_ if hasattr(field, 'outer_type_') else field.type_
    except (ImportError, TypeError):
        pass
    
    # Try dataclass
    try:
        from dataclasses import fields
        import typing
        if hasattr(schema, '__dataclass_fields__'):
            for f in fields(schema):
                types[f.name] = f.type
                # Handle Optional types
                if hasattr(typing, 'get_origin') and typing.get_origin(f.type) is Union:
                    args = typing.get_args(f.type)
                    if len(args) == 2 and type(None) in args:
                        types[f.name] = [a for a in args if a is not type(None)][0]
    except Exception:
        pass
    
    return types


def _get_field_defaults(schema: Union[Type, Any]) -> Dict[str, Any]:
    """Extract default values from schema."""
    defaults = {}
    
    # Try Pydantic
    try:
        from pydantic import BaseModel
        if issubclass(schema, BaseModel):
            for name, field in schema.__fields__.items():
                if not field.required and hasattr(field, 'default'):
                    defaults[name] = field.default
    except (ImportError, TypeError):
        pass
    
    # Try dataclass
    try:
        from dataclasses import fields, MISSING
        if hasattr(schema, '__dataclass_fields__'):
            for f in fields(schema):
                if f.default != MISSING:
                    defaults[f.name] = f.default
                elif f.default_factory != MISSING:
                    defaults[f.name] = f.default_factory()
    except Exception:
        pass
    
    return defaults
