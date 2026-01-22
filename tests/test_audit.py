"""Tests for audit system."""
import pytest
import tempfile
import os
from src.env_loader_pro.core.loader import load_env
from src.env_loader_pro.core.audit import ConfigAudit, AuditEntry
from datetime import datetime


def test_audit_basic():
    """Test basic audit functionality."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
        f.write("PORT=8080\nAPI_KEY=secret123")
        f.flush()
        
        result = load_env(path=f.name, audit=True)
        
        # Should return tuple
        assert isinstance(result, tuple)
        config, audit = result
        
        # Audit should have entries
        assert len(audit.entries) > 0
        assert "PORT" in audit.entries
        assert "API_KEY" in audit.entries
        
        # Check audit entry
        entry = audit.get("PORT")
        assert entry is not None
        assert entry.key == "PORT"
        assert entry.source in ["file", "system"]
        assert entry.masked == False  # PORT is not a secret
        
        # API_KEY should be marked as masked
        api_entry = audit.get("API_KEY")
        assert api_entry.masked == True
        
        os.unlink(f.name)


def test_audit_json_export():
    """Test audit JSON export."""
    audit = ConfigAudit()
    audit.add("TEST_KEY", "file", masked=False)
    audit.add("SECRET_KEY", "azure", provider="AzureKeyVaultProvider", masked=True)
    
    json_str = audit.to_json()
    assert "TEST_KEY" in json_str
    assert "SECRET_KEY" in json_str
    assert "azure" in json_str
    # Should not contain actual secret values
    assert "secret" not in json_str.lower() or "****" in json_str


def test_audit_summary():
    """Test audit summary statistics."""
    audit = ConfigAudit()
    audit.add("KEY1", "file", masked=False)
    audit.add("KEY2", "azure", provider="AzureKeyVaultProvider", masked=True)
    audit.add("KEY3", "aws", provider="AWSSecretsManagerProvider", masked=True)
    
    summary = audit.get_summary()
    assert summary["total_variables"] == 3
    assert summary["masked_variables"] == 2
    assert "file" in summary["sources"]
    assert "azure" in summary["sources"]
    assert "aws" in summary["sources"]


def test_audit_ci_mode():
    """Test audit in CI mode (no providers)."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
        f.write("PORT=8080")
        f.flush()
        
        result = load_env(path=f.name, audit=True, providers=[])
        config, audit = result
        
        # Should work without providers
        assert len(audit.entries) > 0
        assert "PORT" in audit.entries
        
        os.unlink(f.name)
