"""Pre-flight checks for a qa-walk run."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["httpx>=0.27", "pyyaml>=6.0.2", "pydantic>=2.9"]
# ///
from __future__ import annotations
import os
import shutil
import sys
from pathlib import Path
import httpx

from validate_auth import validate_auth_file, AuthValidationError
from validate_workflows import validate_workflows_file, WorkflowValidationError

DEV_SERVER_PROBE_BODY_MARKER = 'id="root"'   # default for Vite/Next/Expo Web


class PreflightError(Exception):
    pass


def _http_get(url: str, timeout: float = 5.0) -> httpx.Response:
    return httpx.get(url, timeout=timeout, follow_redirects=True)


def preflight(
    *,
    qa_dir: Path,
    app: str,
    runner: str,
    probe_url: str | None,
    probe_marker: str = DEV_SERVER_PROBE_BODY_MARKER,
) -> dict:
    """Run pre-flight; raise PreflightError on any failure with actionable message."""
    # auth.yaml exists + valid
    auth_path = qa_dir / "auth.yaml"
    if not auth_path.exists():
        raise PreflightError(
            f"{auth_path} missing. Copy .agents/skills/qa-walk/templates/auth.yaml.example "
            f"to {auth_path} and fill in env vars."
        )
    try:
        auth = validate_auth_file(auth_path)
    except AuthValidationError as e:
        raise PreflightError(f"auth.yaml invalid: {e}") from e

    # workflows.yaml exists + valid
    wf_path = qa_dir / "workflows.yaml"
    if not wf_path.exists():
        raise PreflightError(
            f"{wf_path} missing. Run the workflow scaffolder first (see SKILL.md)."
        )
    try:
        workflows = validate_workflows_file(wf_path, set(auth.personas.keys()))
    except WorkflowValidationError as e:
        raise PreflightError(f"workflows.yaml invalid: {e}") from e

    # Codex installed + Playwright MCP wired if runner=codex
    if runner == "codex":
        if shutil.which("codex") is None:
            raise PreflightError(
                "runner=codex but `codex` not on PATH. Install Codex CLI or run with --runner claude."
            )
        # Codex ships with NO MCPs by default - Playwright must be wired or the agent has no browser.
        # Validated on a local walk: missing playwright MCP caused 126K wasted tokens
        # before the agent realized it couldn't browse.
        import subprocess
        try:
            mcp_list = subprocess.run(
                ["codex", "mcp", "list"], capture_output=True, text=True, timeout=10
            ).stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise PreflightError(f"`codex mcp list` failed: {e}") from e
        if "playwright" not in mcp_list:
            raise PreflightError(
                "runner=codex but Playwright MCP not configured. Run once:\n"
                "  codex mcp add playwright -- npx -y @playwright/mcp@latest\n"
                "Then re-run qa-walk."
            )

    # Dev server probe
    if probe_url:
        try:
            resp = _http_get(probe_url)
        except Exception as e:
            raise PreflightError(f"dev-server probe failed: {probe_url}: {e}") from e
        if resp.status_code != 200:
            raise PreflightError(
                f"dev-server probe returned {resp.status_code} from {probe_url}; expected 200"
            )
        if probe_marker and probe_marker not in resp.text:
            raise PreflightError(
                f"dev-server probe at {probe_url} returned 200 but body marker "
                f"{probe_marker!r} not found - server may be serving a CDN default page"
            )

    return {
        "auth": auth.model_dump(),
        "workflows": workflows.model_dump(),
        "personas": list(auth.personas.keys()),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-dir", required=True)
    parser.add_argument("--app", required=True)
    parser.add_argument("--runner", default="codex", choices=["codex", "claude"])
    parser.add_argument("--probe-url", default=None)
    parser.add_argument("--probe-marker", default=DEV_SERVER_PROBE_BODY_MARKER)
    args = parser.parse_args()
    try:
        preflight(
            qa_dir=Path(args.qa_dir), app=args.app, runner=args.runner,
            probe_url=args.probe_url, probe_marker=args.probe_marker,
        )
        print("preflight ok")
    except PreflightError as e:
        print(f"preflight failed: {e}", file=sys.stderr)
        sys.exit(1)
