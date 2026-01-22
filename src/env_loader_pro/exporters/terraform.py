"""Export configuration to Terraform .tfvars format."""

from typing import Any, Dict, Optional


def export_tfvars(
    config: Dict[str, Any],
    output_path: str = "terraform.tfvars",
    sensitive_keys: Optional[list] = None,
) -> None:
    """Export configuration as Terraform .tfvars file.
    
    Args:
        config: Configuration dictionary
        output_path: Output file path
        sensitive_keys: Optional list of keys to mark as sensitive (commented out)
    """
    sensitive_keys = set(sensitive_keys or [])
    
    lines = []
    lines.append("# Terraform variables")
    lines.append("# Generated from env-loader-pro")
    lines.append("")
    
    for key, value in sorted(config.items()):
        is_sensitive = key in sensitive_keys
        
        if is_sensitive:
            lines.append(f"# {key} = \"<sensitive>\"  # Set this value manually")
        else:
            # Format value appropriately
            if isinstance(value, str):
                # Escape quotes
                value_str = value.replace('"', '\\"')
                lines.append(f'{key} = "{value_str}"')
            elif isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"{key} = {value}")
            elif isinstance(value, list):
                # Convert list to HCL format
                items = [f'"{item}"' if isinstance(item, str) else str(item) for item in value]
                lines.append(f"{key} = [{', '.join(items)}]")
            else:
                lines.append(f'{key} = "{str(value)}"')
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_tfvars_json(
    config: Dict[str, Any],
    output_path: str = "terraform.tfvars.json",
) -> None:
    """Export configuration as Terraform .tfvars.json file.
    
    Args:
        config: Configuration dictionary
        output_path: Output file path
    """
    import json
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
