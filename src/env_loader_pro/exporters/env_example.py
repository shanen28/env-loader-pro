"""Generate .env.example files from schema."""

from typing import Any, Callable, Dict, Iterable, Mapping, Optional


def generate_env_example(
    required: Optional[Iterable[str]] = None,
    optional: Optional[Iterable[str]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    types: Optional[Mapping[str, Callable]] = None,
    output_path: str = ".env.example",
    comments: Optional[Mapping[str, str]] = None,
) -> None:
    """Generate a .env.example file from schema.
    
    Args:
        required: Required variable names
        optional: Optional variable names
        defaults: Default values
        types: Type mapping
        output_path: Output file path
        comments: Optional comments per variable
    """
    lines = []
    lines.append("# Environment Configuration")
    lines.append("# Copy this file to .env and fill in your values")
    lines.append("")
    
    all_vars = set(required or []) | set(optional or []) | set(defaults.keys()) | set(types.keys())
    comments = comments or {}
    
    if required:
        lines.append("# Required variables")
        for var in sorted(required):
            default_val = defaults.get(var, "")
            type_hint = types.get(var, str)
            comment = comments.get(var, f"  # {type_hint.__name__}")
            lines.append(f"{var}={default_val}{comment}")
        lines.append("")
    
    if optional:
        lines.append("# Optional variables")
        for var in sorted(optional):
            if var not in required:
                default_val = defaults.get(var, "")
                type_hint = types.get(var, str)
                comment = comments.get(var, f"  # {type_hint.__name__}")
                lines.append(f"{var}={default_val}{comment}")
        lines.append("")
    
    # Other variables from defaults/types
    other_vars = (set(defaults.keys()) | set(types.keys())) - set(required or []) - set(optional or [])
    if other_vars:
        lines.append("# Additional variables")
        for var in sorted(other_vars):
            default_val = defaults.get(var, "")
            type_hint = types.get(var, str)
            comment = comments.get(var, f"  # {type_hint.__name__}")
            lines.append(f"{var}={default_val}{comment}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
