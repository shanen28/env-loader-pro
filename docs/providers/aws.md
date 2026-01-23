# AWS Providers

Load secrets from AWS Secrets Manager or AWS Systems Manager Parameter Store.

## Installation

```bash
pip install env-loader-pro[aws]
```

## AWS Secrets Manager

### Basic Usage

```python
from env_loader_pro import load_env
from env_loader_pro.providers import AWSSecretsManagerProvider

# Create provider
provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod",
    region="us-east-1"
)

# Load configuration
config = load_env(
    env="prod",
    providers=[provider]
)
```

### JSON Secrets

If secret is JSON, extracts individual fields:

```python
# AWS Secret: {"DB_PASSWORD": "secret", "API_KEY": "key"}
provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod"
)

config = load_env(providers=[provider])
# config["DB_PASSWORD"] = "secret"
# config["API_KEY"] = "key"
```

### Plain Text Secrets

```python
# AWS Secret: plain text value
provider = AWSSecretsManagerProvider(
    secret_id="myapp/api-key"  # Secret name
)

config = load_env(providers=[provider])
# config["myapp/api-key"] = "value"
```

## AWS SSM Parameter Store

### Basic Usage

```python
from env_loader_pro.providers import AWSSSMProvider

# Create provider
provider = AWSSSMProvider(
    prefix="/myapp/prod/",
    region="us-east-1"
)

# Load configuration
config = load_env(providers=[provider])
```

### Parameter Names

```python
# SSM Parameters:
# /myapp/prod/DB_PASSWORD
# /myapp/prod/API_KEY

provider = AWSSSMProvider(prefix="/myapp/prod/")

config = load_env(providers=[provider])
# config["DB_PASSWORD"] = value from /myapp/prod/DB_PASSWORD
# config["API_KEY"] = value from /myapp/prod/API_KEY
```

### Get All Parameters

```python
provider = AWSSSMProvider(prefix="/myapp/prod/")

# Automatically loads all parameters under prefix
config = load_env(providers=[provider])
```

## Authentication

Uses boto3 default credential chain:

1. **IAM Role** - EC2, ECS, Lambda (recommended)
2. **Environment Variables** - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
3. **AWS Credentials File** - `~/.aws/credentials`
4. **IAM Instance Profile** - EC2 instance profile

## Caching

```python
provider = AWSSecretsManagerProvider(
    secret_id="myapp/prod",
    cache=True,
    cache_ttl=3600
)
```

## Failure Policy

```python
config = load_env(
    providers=[aws_provider],
    failure_policy={
        "aws": "fallback"  # Continue if AWS unavailable
    }
)
```

## Example

```python
from env_loader_pro import load_env
from env_loader_pro.providers import (
    AWSSecretsManagerProvider,
    AWSSSMProvider
)

# Use both providers
secrets_provider = AWSSecretsManagerProvider(
    secret_id="myapp/secrets",
    region="us-east-1"
)

ssm_provider = AWSSSMProvider(
    prefix="/myapp/config/",
    region="us-east-1"
)

config = load_env(
    env="prod",
    providers=[secrets_provider, ssm_provider],
    audit=True
)
```

## Best Practices

1. **Use IAM roles** in production (no static credentials)
2. **Enable caching** to reduce API calls
3. **Use prefixes** for SSM parameters
4. **Set failure policy** based on environment
5. **Enable audit** for compliance

## Related Topics

- [Providers Overview](../providers/overview.md)
- [Failure Policies](../enterprise/policies.md)
