# Exporters API

Export configuration to various formats.

## Export to JSON

```python
config = load_env()
config.save("config.json", format="json")
```

## Export to YAML

```python
config = load_env()
config.save("config.yaml", format="yaml")
```

## Export to Kubernetes

```python
from env_loader_pro.exporters import export_kubernetes

config = load_env()
export_kubernetes(config, output_path="k8s-config")
```

## Export to Terraform

```python
from env_loader_pro.exporters import export_tfvars

config = load_env()
export_tfvars(config, output_path="terraform.tfvars")
```

## Generate .env.example

```python
from env_loader_pro.exporters import generate_env_example

generate_env_example(
    required=["API_KEY", "PORT"],
    optional=["DEBUG"],
    output_path=".env.example"
)
```

## Related Topics

- [CLI Commands](../cli/commands.md)
