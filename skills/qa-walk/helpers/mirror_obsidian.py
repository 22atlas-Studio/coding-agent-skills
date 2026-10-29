"""Copy a brief.md under $QA_NOTES_DIR/QA/<app>/<run_ts>/."""
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
from __future__ import annotations
import os
import shutil
import sys
from pathlib import Path


def notes_root_from_env() -> Path | None:
    raw = os.environ.get("QA_NOTES_DIR", "").strip()
    if not raw:
        return None
    return Path(raw)


def mirror_brief_to_obsidian(
    brief_path: Path, app: str, run_ts: str,
    vault_root: Path | None = None,
) -> Path | None:
    if vault_root is None:
        vault_root = notes_root_from_env()
    if vault_root is None or not vault_root.exists():
        shown = vault_root if vault_root is not None else "$QA_NOTES_DIR"
        print(f"qa-walk: vault unreachable at {shown}; skipping mirror", file=sys.stderr)
        return None
    dest_dir = vault_root / "QA" / app / run_ts
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "brief.md"
    shutil.copy2(brief_path, dest)
    return dest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("brief")
    parser.add_argument("app")
    parser.add_argument("run_ts")
    parser.add_argument("--vault-root", default=os.environ.get("QA_NOTES_DIR", ""))
    args = parser.parse_args()
    root = Path(args.vault_root) if args.vault_root else None
    out = mirror_brief_to_obsidian(Path(args.brief), args.app, args.run_ts, root)
    print(out or "(skipped)")
