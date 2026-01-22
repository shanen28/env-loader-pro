"""Tests for policy-as-code."""
import pytest
import tempfile
import json
import os
from src.env_loader_pro.core.policy_code import Policy, load_policy
from src.env_loader_pro.exceptions import ValidationError


def test_policy_from_dict():
    """Test creating policy from dictionary."""
    policy_dict = {
        "require": ["API_KEY", "DB_PASSWORD"],
        "forbid": ["DEBUG"],
        "ttl": {"API_KEY": 3600},
        "sources": {"DB_PASSWORD": "azure"}
    }
    
    policy = Policy.from_dict(policy_dict)
    assert "API_KEY" in policy.require
    assert "DB_PASSWORD" in policy.require
    assert "DEBUG" in policy.forbid
    assert policy.ttl["API_KEY"] == 3600


def test_policy_validation_require():
    """Test policy validation for required variables."""
    policy = Policy(require=["API_KEY", "DB_PASSWORD"])
    
    # Missing required
    with pytest.raises(ValidationError):
        policy.validate({"PORT": 8080})
    
    # All required present
    policy.validate({"API_KEY": "key", "DB_PASSWORD": "pass"})


def test_policy_validation_forbid():
    """Test policy validation for forbidden variables."""
    policy = Policy(forbid=["DEBUG"])
    
    # Forbidden present
    with pytest.raises(ValidationError):
        policy.validate({"DEBUG": True})
    
    # Forbidden not present
    policy.validate({"PORT": 8080})


def test_policy_from_json_file():
    """Test loading policy from JSON file."""
    policy_dict = {
        "require": ["API_KEY"],
        "forbid": ["DEBUG"]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(policy_dict, f)
        f.flush()
        
        policy = Policy.from_file(f.name)
        assert "API_KEY" in policy.require
        assert "DEBUG" in policy.forbid
        
        os.unlink(f.name)


def test_policy_to_dict():
    """Test policy to dictionary conversion."""
    policy = Policy(
        require=["API_KEY"],
        forbid=["DEBUG"],
        ttl={"API_KEY": 3600}
    )
    
    policy_dict = policy.to_dict()
    assert "require" in policy_dict
    assert "forbid" in policy_dict
    assert "ttl" in policy_dict
    assert policy_dict["require"] == ["API_KEY"]
