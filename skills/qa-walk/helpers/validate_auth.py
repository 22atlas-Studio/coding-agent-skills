"""Validate qa/auth.yaml against schema + environment."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["pydantic>=2.9", "pyyaml>=6.0.2"]
# ///
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Literal
import yaml
from pydantic import BaseModel, ValidationError, model_validator


class AuthValidationError(Exception):
    """Raised when auth.yaml fails validation."""


class LoginEmailPassword(BaseModel):
    type: Literal["email_password"]
    route: str
    success_marker: str


class LoginMagicLink(BaseModel):
    type: Literal["magic_link"]
    mailbox_url: str
    success_marker: str


class LoginAnonymousThenUpgrade(BaseModel):
    type: Literal["anonymous_then_upgrade"]
    success_marker: str


class Bypass(BaseModel):
    type: Literal["sql", "http", "none"]
    command: str | None = None


class Persona(BaseModel):
    email: str
    password_env: str
    login: LoginEmailPassword | LoginMagicLink | LoginAnonymousThenUpgrade
    bypass: Bypass | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_inline_password(cls, data: Any) -> Any:
        if isinstance(data, dict) and "password" in data:
            raise ValueError(
                "inline password forbidden - use password_env to reference an env var name only"
            )
        return data


class AuthFile(BaseModel):
    personas: dict[str, Persona]


def validate_auth_file(path: Path) -> AuthFile:
    raw = yaml.safe_load(path.read_text())
    try:
        auth = AuthFile.model_validate(raw)
    except ValidationError as e:
        msg = str(e)
        if "inline password" in msg:
            raise AuthValidationError(f"{path}: inline password forbidden") from e
        if "login.type" in msg or "Input tag" in msg:
            raise AuthValidationError(f"{path}: unknown login.type") from e
        raise AuthValidationError(f"{path}: {msg}") from e

    for name, persona in auth.personas.items():
        value = os.environ.get(persona.password_env, "").strip()
        if not value:
            raise AuthValidationError(
                f"{path}: persona '{name}' references env var "
                f"{persona.password_env!r} which is unset or empty"
            )
    return auth


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("usage: validate_auth.py <path-to-auth.yaml>", file=sys.stderr)
        sys.exit(2)
    try:
        validate_auth_file(Path(sys.argv[1]))
        print("ok")
    except AuthValidationError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
