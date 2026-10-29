"""Shared pytest fixtures for qa-walk helpers."""
from pathlib import Path
import pytest

@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def tmp_qa_dir(tmp_path: Path) -> Path:
    qa = tmp_path / "qa"
    qa.mkdir()
    (qa / "runs").mkdir()
    return qa
