# Docker & Kubernetes Providers

Load secrets from Docker and Kubernetes mounted volumes.

## Docker Secrets

Docker Swarm mounts secrets at `/run/secrets/`.

### Basic Usage

```python
from env_loader_pro import load_env
from env_loader_pro.providers import DockerSecretsProvider

# Create provider (defaults to /run/secrets)
provider = DockerSecretsProvider()

# Or custom path
provider = DockerSecretsProvider(secrets_path="/custom/secrets")

# Load configuration
config = load_env(providers=[provider])
```

### Auto-Detection

Docker secrets are automatically detected if available:

```python
# Automatically loads from /run/secrets if available
config = load_env(env="prod")
```

## Kubernetes Secrets

Kubernetes mounts secrets and configmaps as files.

### Basic Usage

```python
from env_loader_pro import load_env
from env_loader_pro.providers import KubernetesSecretsProvider

# Create provider
provider = KubernetesSecretsProvider(
    secrets_path="/etc/secrets",      # K8s secrets mount
    config_map_path="/etc/config"    # K8s configmap mount
)

# Load configuration
config = load_env(providers=[provider])
```

### Auto-Detection

Kubernetes secrets are automatically detected if available:

```python
# Automatically loads from /etc/secrets and /etc/config if available
config = load_env(env="prod")
```

## Filesystem Provider

Generic filesystem-mounted configuration:

```python
from env_loader_pro.providers import FilesystemProvider

provider = FilesystemProvider(
    secrets_path="/etc/secrets",
    config_map_path="/etc/config"
)

config = load_env(providers=[provider])
```

## Kubernetes Deployment Example

### Secret Definition

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  DB_PASSWORD: <base64-encoded>
  API_KEY: <base64-encoded>
```

### Pod Mount

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
```

### Application Code

```python
from env_loader_pro import load_env

# Automatically loads from /etc/secrets
config = load_env(env="prod")
db_password = config["DB_PASSWORD"]  # From mounted secret
```

## Priority

Docker/K8s secrets have priority 3 (after cloud providers and system env):

1. Cloud providers
2. System environment
3. **Docker/K8s secrets** ← Here
4. .env files
5. Schema defaults

## Best Practices

1. **Use K8s secrets** for sensitive data
2. **Use configmaps** for non-sensitive config
3. **Mount read-only** volumes
4. **Enable audit** to track sources
5. **Test locally** with Docker secrets

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Configuration Precedence](../core-concepts/precedence.md)
