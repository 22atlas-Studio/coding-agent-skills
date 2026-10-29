"""Tests for auth.yaml validator."""
import os
import pytest
from validate_auth import validate_auth_file, AuthValidationError

def test_valid_auth_passes(fixtures_dir, monkeypatch):
    monkeypatch.setenv("QA_DEALER_PASSWORD", "shh")
    result = validate_auth_file(fixtures_dir / "valid_auth.yaml")
    assert "dealer" in result.personas
    assert result.personas["dealer"].email == "operator@example.test"

def test_inline_password_rejected(fixtures_dir):
    with pytest.raises(AuthValidationError, match="inline password"):
        validate_auth_file(fixtures_dir / "invalid_auth_inline_password.yaml")

def test_unknown_login_type_rejected(fixtures_dir, monkeypatch):
    monkeypatch.setenv("QA_DEALER_PASSWORD", "shh")
    with pytest.raises(AuthValidationError, match="login.type"):
        validate_auth_file(fixtures_dir / "invalid_auth_unknown_login_type.yaml")

def test_missing_password_env_var_rejected(fixtures_dir, monkeypatch):
    monkeypatch.delenv("QA_DEALER_PASSWORD", raising=False)
    with pytest.raises(AuthValidationError, match="QA_DEALER_PASSWORD"):
        validate_auth_file(fixtures_dir / "valid_auth.yaml")

def test_empty_password_env_var_rejected(fixtures_dir, monkeypatch):
    monkeypatch.setenv("QA_DEALER_PASSWORD", "  ")
    with pytest.raises(AuthValidationError, match="QA_DEALER_PASSWORD"):
        validate_auth_file(fixtures_dir / "valid_auth.yaml")
