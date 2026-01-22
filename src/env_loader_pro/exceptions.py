"""Custom exceptions for env-loader-pro."""


class EnvLoaderError(Exception):
    """Base exception for env-loader-pro errors."""
    pass


class ValidationError(EnvLoaderError):
    """Raised when validation fails."""
    pass


class ProviderError(EnvLoaderError):
    """Raised when a provider fails."""
    pass


class DecryptionError(EnvLoaderError):
    """Raised when decryption fails."""
    pass


class SchemaError(EnvLoaderError):
    """Raised when schema validation fails."""
    pass


class ConfigurationError(EnvLoaderError):
    """Raised when configuration is invalid."""
    pass
