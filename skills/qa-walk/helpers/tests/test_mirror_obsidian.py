from pathlib import Path
from mirror_obsidian import mirror_brief_to_obsidian


def test_mirror_writes_to_expected_vault_path(tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text("# QA Walk: example-app - 2026-05-10-1430\n\nbody")

    vault_root = tmp_path / "vault"
    vault_root.mkdir()

    out = mirror_brief_to_obsidian(
        brief_path=brief,
        app="example-app",
        run_ts="2026-05-10-1430",
        vault_root=vault_root,
    )
    expected = vault_root / "QA" / "example-app" / "2026-05-10-1430" / "brief.md"
    assert out == expected
    assert expected.read_text() == brief.read_text()


def test_mirror_creates_parents_idempotent(tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text("body")
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    mirror_brief_to_obsidian(brief, "example-app", "ts1", vault_root)
    mirror_brief_to_obsidian(brief, "example-app", "ts1", vault_root)


def test_mirror_skips_when_vault_unreachable(tmp_path, capsys):
    brief = tmp_path / "brief.md"
    brief.write_text("body")
    out = mirror_brief_to_obsidian(brief, "example-app", "ts", Path("/no/such/vault/root"))
    assert out is None
    captured = capsys.readouterr()
    assert "vault unreachable" in captured.err
