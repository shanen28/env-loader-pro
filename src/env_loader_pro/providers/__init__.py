"""Provider system for loading configuration from multiple sources."""

from ..exceptions import ProviderError
from .base import BaseProvider

try:
    from .azure import AzureKeyVaultProvider
except ImportError:
    AzureKeyVaultProvider = None

try:
    from .aws import AWSSecretsManagerProvider, AWSSSMProvider
except ImportError:
    AWSSecretsManagerProvider = None
    AWSSSMProvider = None

try:
    from .docker import DockerSecretsProvider, KubernetesSecretsProvider
except ImportError:
    DockerSecretsProvider = None
    KubernetesSecretsProvider = None

try:
    from .filesystem import FilesystemProvider
except ImportError:
    FilesystemProvider = None

__all__ = [
    "BaseProvider",
    "ProviderError",
    "AzureKeyVaultProvider",
    "AWSSecretsManagerProvider",
    "AWSSSMProvider",
    "DockerSecretsProvider",
    "KubernetesSecretsProvider",
    "FilesystemProvider",
]

