# .claude/skills/security-scan/tests/test_pre_pass.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from pre_pass import run_pre_pass  # noqa: E402

def _prefix() -> str:
    return "sk-" + "ant-"


PATTERNS = {
    "patterns": [
        {
            "rule_name": "hardcoded_secret_prefix",
            "substrings": [_prefix(), "AK" + "IA"],
            "reminder": "Possible hardcoded credential.",
        },
        {
            "rule_name": "service_role_in_client",
            "regex": "SERVICE_ROLE|service_role",
            "paths": ["**/app/**"],
            "exclude_paths": ["**/supabase/functions/**", "**/*.test.*"],
            "reminder": "Service-role usage in client code.",
        },
    ]
}


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_substring_secret_flagged(tmp_path: Path):
    _write(tmp_path, "app/config.ts", 'const k = "' + _prefix() + 'abc123";\n')
    findings = run_pre_pass(tmp_path, PATTERNS)
    assert len(findings) == 1
    f = findings[0]
    assert f["severity"] == "critical"
    assert f["category"] == "hardcoded_secret_prefix"
    assert f["file"] == "app/config.ts"
    assert f["start_line"] == 1
    assert f["confidence"] == "high"


def test_service_role_path_gating(tmp_path: Path):
    _write(tmp_path, "app/db.ts", "const c = service_role;\n")
    _write(tmp_path, "app/db.test.ts", "const c = service_role;\n")
    _write(tmp_path, "supabase/functions/x.ts", "const c = service_role;\n")
    findings = run_pre_pass(tmp_path, PATTERNS)
    files = sorted(f["file"] for f in findings)
    assert files == ["app/db.ts"]  # test file + edge function excluded


def test_ignored_dirs_skipped(tmp_path: Path):
    _write(tmp_path, "node_modules/pkg/index.ts", 'const k = "' + _prefix() + 'x";\n')
    findings = run_pre_pass(tmp_path, PATTERNS)
    assert findings == []


def test_clean_repo_empty(tmp_path: Path):
    _write(tmp_path, "app/clean.ts", "const k = 1;\n")
    assert run_pre_pass(tmp_path, PATTERNS) == []


def test_relative_root_does_not_crash(tmp_path: Path, monkeypatch):
    # The SKILL.md driver invokes pre_pass with a RELATIVE root
    # (e.g. a downstream app directory). _iter_files resolves the root to
    # absolute, so run_pre_pass must resolve too or relative_to() raises.
    _write(tmp_path, "app/config.ts", 'const k = "' + _prefix() + 'rel";\n')
    monkeypatch.chdir(tmp_path)
    findings = run_pre_pass(Path("."), PATTERNS)
    assert any(f["category"] == "hardcoded_secret_prefix" for f in findings)
    assert findings[0]["file"] == "app/config.ts"
