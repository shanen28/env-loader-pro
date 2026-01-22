"""Tests for failure policy system."""
import pytest
from src.env_loader_pro.core.policy import PolicyManager, FailurePolicy, ProviderResult
from src.env_loader_pro.exceptions import ProviderError


def test_policy_manager_default():
    """Test default policy manager."""
    manager = PolicyManager()
    policy = manager.get_policy("AzureKeyVaultProvider")
    # Should use default policy
    assert policy in [FailurePolicy.FAIL, FailurePolicy.WARN, FailurePolicy.FALLBACK]


def test_policy_manager_custom():
    """Test custom policies."""
    policies = {
        "azure": "fail",
        "aws": "warn",
        "filesystem": "fallback"
    }
    manager = PolicyManager(policies=policies)
    
    assert manager.get_policy("AzureKeyVaultProvider") == FailurePolicy.FAIL
    assert manager.get_policy("AWSSecretsManagerProvider") == FailurePolicy.WARN
    assert manager.get_policy("FilesystemProvider") == FailurePolicy.FALLBACK


def test_policy_fail():
    """Test fail policy raises error."""
    manager = PolicyManager(policies={"test": "fail"})
    
    with pytest.raises(ProviderError):
        manager.handle_error("test", Exception("Test error"))


def test_policy_warn():
    """Test warn policy logs but continues."""
    manager = PolicyManager(policies={"test": "warn"})
    
    # Should not raise
    try:
        manager.handle_error("test", Exception("Test error"))
    except ProviderError:
        pytest.fail("Warn policy should not raise")


def test_policy_fallback():
    """Test fallback policy silently continues."""
    manager = PolicyManager(policies={"test": "fallback"})
    
    # Should not raise
    try:
        manager.handle_error("test", Exception("Test error"))
    except ProviderError:
        pytest.fail("Fallback policy should not raise")


def test_provider_result():
    """Test ProviderResult."""
    result = ProviderResult(data={"KEY": "value"})
    assert result.is_success()
    assert not result.has_errors()
    
    result_with_errors = ProviderResult(data={}, errors=[Exception("Error")])
    assert not result_with_errors.is_success()
    assert result_with_errors.has_errors()
