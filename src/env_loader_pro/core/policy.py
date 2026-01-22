"""Failure policy control for provider error handling."""

from enum import Enum
from typing import Any, Dict, List, Optional

from ..exceptions import ProviderError
from ..utils.logging import get_logger


class FailurePolicy(Enum):
    """Failure policy types."""
    
    FAIL = "fail"  # Raise error
    WARN = "warn"  # Log warning and continue
    FALLBACK = "fallback"  # Silently continue (use fallback)


class ProviderResult:
    """Result from a provider operation."""
    
    def __init__(
        self,
        data: Dict[str, str],
        errors: Optional[List[Exception]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize provider result.
        
        Args:
            data: Configuration data dictionary
            errors: Optional list of errors encountered
            metadata: Optional metadata about the operation
        """
        self.data = data
        self.errors = errors or []
        self.metadata = metadata or {}
    
    def has_errors(self) -> bool:
        """Check if result has errors.
        
        Returns:
            True if errors present
        """
        return len(self.errors) > 0
    
    def is_success(self) -> bool:
        """Check if result is successful.
        
        Returns:
            True if no errors
        """
        return not self.has_errors()


class PolicyManager:
    """Manages failure policies for providers."""
    
    def __init__(
        self,
        policies: Optional[Dict[str, str]] = None,
        default_policy: str = "warn",
    ):
        """Initialize policy manager.
        
        Args:
            policies: Dictionary mapping provider names to policies
            default_policy: Default policy for providers not in policies
        """
        self.policies: Dict[str, FailurePolicy] = {}
        self.default_policy = FailurePolicy(default_policy)
        
        if policies:
            for provider, policy_str in policies.items():
                try:
                    self.policies[provider] = FailurePolicy(policy_str.lower())
                except ValueError:
                    # Invalid policy, use default
                    self.policies[provider] = self.default_policy
    
    def get_policy(self, provider_name: str) -> FailurePolicy:
        """Get failure policy for a provider.
        
        Args:
            provider_name: Provider name or class name
        
        Returns:
            FailurePolicy enum
        """
        # Try exact match first
        if provider_name in self.policies:
            return self.policies[provider_name]
        
        # Try partial match (e.g., "AzureKeyVaultProvider" -> "azure")
        provider_lower = provider_name.lower()
        for key, policy in self.policies.items():
            if key.lower() in provider_lower or provider_lower in key.lower():
                return policy
        
        return self.default_policy
    
    def handle_error(
        self,
        provider_name: str,
        error: Exception,
        context: Optional[str] = None,
    ) -> None:
        """Handle provider error according to policy.
        
        Args:
            provider_name: Provider name
            error: Exception that occurred
            context: Optional context string
        
        Raises:
            ProviderError: If policy is FAIL
        """
        policy = self.get_policy(provider_name)
        logger = get_logger()
        
        error_msg = f"Provider {provider_name} error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        if policy == FailurePolicy.FAIL:
            raise ProviderError(error_msg) from error
        elif policy == FailurePolicy.WARN:
            logger.warning(error_msg, provider=provider_name, error=str(error))
        elif policy == FailurePolicy.FALLBACK:
            logger.debug(error_msg, provider=provider_name, error=str(error))
        # FALLBACK: silently continue (already logged at debug level)
    
    def should_continue(self, provider_name: str) -> bool:
        """Check if should continue after error for a provider.
        
        Args:
            provider_name: Provider name
        
        Returns:
            True if should continue (not FAIL policy)
        """
        policy = self.get_policy(provider_name)
        return policy != FailurePolicy.FAIL


def create_default_policies() -> Dict[str, str]:
    """Create default failure policies for common scenarios.
    
    Returns:
        Dictionary of default policies
    """
    return {
        "azure": "fail",  # Production: fail on Azure errors
        "aws": "fallback",  # Fallback if AWS unavailable
        "filesystem": "warn",  # Warn on filesystem errors
        "docker": "warn",  # Warn on Docker secret errors
        "kubernetes": "warn",  # Warn on K8s errors
    }
