"""env_loader_pro — enterprise-ready typed environment loader"""

# Core exports
from .core.loader import load_env
from .exceptions import (
    ConfigurationError,
    DecryptionError,
    EnvLoaderError,
    ProviderError,
    SchemaError,
    ValidationError,
)

# Schema support (backward compatibility)
from .schema import load_with_schema

# Exporters
from .exporters import (
    export_configmap,
    export_kubernetes,
    export_secret,
    export_tfvars,
    export_tfvars_json,
    generate_env_example,
)

# Provider exports
try:
    from .providers import (
        BaseProvider,
        AzureKeyVaultProvider,
        AWSSecretsManagerProvider,
        AWSSSMProvider,
        DockerSecretsProvider,
        FilesystemProvider,
        KubernetesSecretsProvider,
    )
    PROVIDERS_AVAILABLE = True
except ImportError:
    PROVIDERS_AVAILABLE = False
    BaseProvider = None

# Integration exports
try:
    from .integrations.fastapi import config_dependency, inject_config
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    config_dependency = None
    inject_config = None

# Watch exports
try:
    from .watch import ConfigReloader, create_reloader
    WATCH_AVAILABLE = True
except ImportError:
    WATCH_AVAILABLE = False
    ConfigReloader = None
    create_reloader = None

# Core utilities
from .core import (
    AuditEntry,
    Cache,
    CircuitBreaker,
    ConfigAudit,
    ConfigDiff,
    ConfigurationMerger,
    FailurePolicy,
    Origin,
    PerformanceMonitor,
    PerformanceSLA,
    Policy,
    PolicyManager,
    ProviderResult,
    SchemaValidator,
    Tracer,
    create_default_policies,
    diff_configs,
    load_policy,
)

# Crypto utilities
try:
    from .crypto import decrypt_file, encrypt_file, re_encrypt_file
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    decrypt_file = None
    encrypt_file = None
    re_encrypt_file = None

# Provider metadata
from .providers.base import ProviderCapabilities, SecretMetadata

# Utils
from .utils import (
    detect_environment,
    get_logger,
    get_recommended_providers,
    is_secret_key,
    mask_dict,
    mask_value,
)

__all__ = [
    # Core API
    "load_env",
    "load_with_schema",
    # Exceptions
    "EnvLoaderError",
    "ValidationError",
    "ProviderError",
    "SchemaError",
    "ConfigurationError",
    "DecryptionError",
    # Exporters
    "generate_env_example",
    "export_configmap",
    "export_secret",
    "export_kubernetes",
    "export_tfvars",
    "export_tfvars_json",
    # Core utilities
    "AuditEntry",
    "Cache",
    "CircuitBreaker",
    "ConfigAudit",
    "ConfigDiff",
    "ConfigurationMerger",
    "FailurePolicy",
    "Origin",
    "PerformanceMonitor",
    "PerformanceSLA",
    "Policy",
    "PolicyManager",
    "ProviderResult",
    "SchemaValidator",
    "Tracer",
    "create_default_policies",
    "diff_configs",
    "load_policy",
    # Providers
    "ProviderCapabilities",
    "SecretMetadata",
    # Utils
    "is_secret_key",
    "mask_dict",
    "mask_value",
    "detect_environment",
    "get_logger",
    "get_recommended_providers",
]

if PROVIDERS_AVAILABLE:
    __all__.extend([
        "BaseProvider",
        "AzureKeyVaultProvider",
        "AWSSecretsManagerProvider",
        "AWSSSMProvider",
        "DockerSecretsProvider",
        "KubernetesSecretsProvider",
        "FilesystemProvider",
    ])

if FASTAPI_AVAILABLE:
    __all__.extend([
        "config_dependency",
        "inject_config",
    ])

if WATCH_AVAILABLE:
    __all__.extend([
        "ConfigReloader",
        "create_reloader",
    ])

if CRYPTO_AVAILABLE:
    __all__.extend([
        "decrypt_file",
        "encrypt_file",
        "re_encrypt_file",
    ])

__version__ = "1.0.1"


