"""Structured logging utilities for env-loader-pro."""

import logging
from typing import Any, Dict, Optional

from ..utils.masking import mask_dict


class EnvLoaderLogger:
    """Structured logger for env-loader-pro."""
    
    def __init__(
        self,
        name: str = "env_loader_pro",
        level: int = logging.INFO,
        mask_secrets: bool = True
    ):
        """Initialize logger.
        
        Args:
            name: Logger name
            level: Logging level
            mask_secrets: Whether to mask secrets in logs
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.mask_secrets = mask_secrets
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal log method with secret masking.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context (will be masked if mask_secrets=True)
        """
        if kwargs and self.mask_secrets:
            # Mask secrets in kwargs
            kwargs = mask_dict(kwargs)
        
        if kwargs:
            # Format kwargs as key=value pairs
            context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {context}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def log_config_load(
        self,
        source: str,
        variable_count: int,
        errors: Optional[list] = None
    ) -> None:
        """Log configuration load event.
        
        Args:
            source: Configuration source name
            variable_count: Number of variables loaded
            errors: Optional list of errors
        """
        self.info(
            f"Loaded configuration from {source}",
            variables=variable_count,
            errors=len(errors) if errors else 0
        )
    
    def log_provider_error(
        self,
        provider: str,
        error: str,
        graceful: bool = True
    ) -> None:
        """Log provider error.
        
        Args:
            provider: Provider name
            error: Error message
            graceful: Whether error was handled gracefully
        """
        level = logging.WARNING if graceful else logging.ERROR
        self.logger.log(
            level,
            f"Provider {provider} error: {error} (graceful={graceful})"
        )


# Default logger instance
_default_logger: Optional[EnvLoaderLogger] = None


def get_logger(name: str = "env_loader_pro") -> EnvLoaderLogger:
    """Get or create default logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = EnvLoaderLogger(name)
    return _default_logger
