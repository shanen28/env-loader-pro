"""Default settings and configuration constants."""

from typing import List

# Default secret patterns for automatic masking
DEFAULT_SECRET_PATTERNS: List[str] = [
    r".*secret.*",
    r".*key.*",
    r".*token.*",
    r".*password.*",
    r".*pwd.*",
    r".*credential.*",
    r".*auth.*",
    r".*api[_-]?key.*",
]

# Default cache TTL (1 hour)
DEFAULT_CACHE_TTL: int = 3600

# Default file paths
DEFAULT_ENV_FILE: str = ".env"
DEFAULT_SECRETS_PATH: str = "/run/secrets"
DEFAULT_K8S_SECRETS_PATH: str = "/etc/secrets"
DEFAULT_K8S_CONFIG_PATH: str = "/etc/config"

# Configuration source priority (lower number = higher priority)
# 1 = highest priority, 6 = lowest priority
SOURCE_PRIORITY = {
    "cloud_providers": 1,  # Azure, AWS
    "system": 2,  # System environment variables
    "docker_k8s": 3,  # Docker/K8s mounted secrets
    "env_specific": 4,  # .env.{env}
    "base_file": 5,  # Base .env
    "schema_defaults": 6,  # Schema defaults
}

# Strict mode settings
STRICT_MODE_DEFAULT: bool = False
STRICT_MODE_WARN_ONLY: bool = True  # Warn instead of fail by default

# Tracing settings
TRACE_DEFAULT: bool = False
TRACE_MASK_SECRETS: bool = True

# Watch settings
WATCH_DEFAULT: bool = False
WATCH_POLL_INTERVAL: float = 1.0  # seconds
