"""Tests for configuration diff/drift detection."""
import pytest
from src.env_loader_pro.core.diff import ConfigDiff, diff_configs
from src.env_loader_pro.utils.masking import is_secret_key


def test_diff_no_changes():
    """Test diff with no changes."""
    current = {"PORT": 8080, "DEBUG": True}
    baseline = {"PORT": 8080, "DEBUG": True}
    
    diff = diff_configs(current, baseline)
    assert not diff.has_changes()
    assert len(diff.added) == 0
    assert len(diff.removed) == 0
    assert len(diff.changed) == 0


def test_diff_added():
    """Test diff with added variables."""
    current = {"PORT": 8080, "NEW_KEY": "value"}
    baseline = {"PORT": 8080}
    
    diff = diff_configs(current, baseline)
    assert diff.has_changes()
    assert "NEW_KEY" in diff.added
    assert len(diff.removed) == 0
    assert len(diff.changed) == 0


def test_diff_removed():
    """Test diff with removed variables."""
    current = {"PORT": 8080}
    baseline = {"PORT": 8080, "OLD_KEY": "value"}
    
    diff = diff_configs(current, baseline)
    assert diff.has_changes()
    assert "OLD_KEY" in diff.removed
    assert len(diff.added) == 0
    assert len(diff.changed) == 0


def test_diff_changed():
    """Test diff with changed variables."""
    current = {"PORT": 9000}
    baseline = {"PORT": 8080}
    
    diff = diff_configs(current, baseline)
    assert diff.has_changes()
    assert "PORT" in diff.changed
    assert len(diff.added) == 0
    assert len(diff.removed) == 0


def test_diff_secret_changes():
    """Test secret change detection."""
    current = {"API_KEY": "new_secret", "PORT": 8080}
    baseline = {"PORT": 8080}
    
    diff = diff_configs(current, baseline)
    secret_changes = diff.get_secret_changes()
    
    if is_secret_key("API_KEY"):
        assert "API_KEY" in secret_changes["added"]


def test_diff_validate_no_secret_changes():
    """Test validation of no secret changes."""
    current = {"PORT": 8080}
    baseline = {"PORT": 8080}
    
    diff = diff_configs(current, baseline)
    # Should not raise
    diff.validate_no_secret_changes()
    
    # With secret added, should raise
    current_with_secret = {"PORT": 8080, "API_KEY": "secret"}
    diff_with_secret = diff_configs(current_with_secret, baseline)
    
    if is_secret_key("API_KEY"):
        with pytest.raises(ValueError, match="Secret changes detected"):
            diff_with_secret.validate_no_secret_changes()
