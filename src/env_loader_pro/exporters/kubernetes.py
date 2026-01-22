"""Export configuration to Kubernetes ConfigMap and Secret YAML."""

from typing import Any, Dict, List, Optional

from ..utils.masking import is_secret_key


def export_configmap(
    config: Dict[str, Any],
    name: str = "app-config",
    namespace: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> str:
    """Export non-secret configuration as Kubernetes ConfigMap YAML.
    
    Args:
        config: Configuration dictionary
        name: ConfigMap name
        namespace: Optional namespace
        labels: Optional labels
    
    Returns:
        YAML string
    """
    # Filter out secrets
    non_secrets = {k: str(v) for k, v in config.items() if not is_secret_key(k)}
    
    yaml_lines = [
        "apiVersion: v1",
        "kind: ConfigMap",
        f"metadata:",
        f"  name: {name}",
    ]
    
    if namespace:
        yaml_lines.append(f"  namespace: {namespace}")
    
    if labels:
        yaml_lines.append("  labels:")
        for key, value in labels.items():
            yaml_lines.append(f"    {key}: {value}")
    
    yaml_lines.append("data:")
    for key, value in sorted(non_secrets.items()):
        # Escape special YAML characters
        value_escaped = str(value).replace('"', '\\"')
        yaml_lines.append(f"  {key}: \"{value_escaped}\"")
    
    return "\n".join(yaml_lines)


def export_secret(
    config: Dict[str, Any],
    name: str = "app-secrets",
    namespace: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
    encode_base64: bool = True,
) -> str:
    """Export secret configuration as Kubernetes Secret YAML.
    
    Args:
        config: Configuration dictionary
        name: Secret name
        namespace: Optional namespace
        labels: Optional labels
        encode_base64: Whether to base64 encode values (K8s requirement)
    
    Returns:
        YAML string
    """
    import base64
    
    # Filter only secrets
    secrets = {k: str(v) for k, v in config.items() if is_secret_key(k)}
    
    yaml_lines = [
        "apiVersion: v1",
        "kind: Secret",
        f"metadata:",
        f"  name: {name}",
    ]
    
    if namespace:
        yaml_lines.append(f"  namespace: {namespace}")
    
    if labels:
        yaml_lines.append("  labels:")
        for key, value in labels.items():
            yaml_lines.append(f"    {key}: {value}")
    
    yaml_lines.append("type: Opaque")
    yaml_lines.append("data:")
    
    for key, value in sorted(secrets.items()):
        if encode_base64:
            encoded = base64.b64encode(value.encode("utf-8")).decode("utf-8")
            yaml_lines.append(f"  {key}: {encoded}")
        else:
            # Kubernetes requires base64, but allow plain for debugging
            value_escaped = str(value).replace('"', '\\"')
            yaml_lines.append(f"  {key}: \"{value_escaped}\"")
    
    return "\n".join(yaml_lines)


def export_kubernetes(
    config: Dict[str, Any],
    configmap_name: str = "app-config",
    secret_name: str = "app-secrets",
    namespace: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, str]:
    """Export configuration as both ConfigMap and Secret.
    
    Args:
        config: Configuration dictionary
        configmap_name: ConfigMap name
        secret_name: Secret name
        namespace: Optional namespace
        output_path: Optional path to write YAML files
    
    Returns:
        Dictionary with 'configmap' and 'secret' keys containing YAML strings
    """
    configmap_yaml = export_configmap(config, configmap_name, namespace)
    secret_yaml = export_secret(config, secret_name, namespace)
    
    if output_path:
        # Write separate files
        configmap_path = f"{output_path}.configmap.yaml"
        secret_path = f"{output_path}.secret.yaml"
        
        with open(configmap_path, "w") as f:
            f.write(configmap_yaml)
        
        with open(secret_path, "w") as f:
            f.write(secret_yaml)
    
    return {
        "configmap": configmap_yaml,
        "secret": secret_yaml,
    }
