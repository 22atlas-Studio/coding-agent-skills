"""Pydantic models for findings.json - emitted by runners, consumed by aggregator."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Verdict = Literal[
    "PASS",
    "BUG",
    "BLOCKED-AUTH",
    "BLOCKED-DEPENDENCY",
    "BLOCKED-BUDGET",
    "BLOCKED-DEV-SERVER",
    "INSPECT",
]

Severity = Literal["critical", "high", "medium", "low"]


class NetworkFailure(BaseModel):
    method: str
    url: str
    status: int
    body_excerpt: str = ""


class Evidence(BaseModel):
    screenshots: list[str] = Field(default_factory=list)
    network_failures: list[NetworkFailure] = Field(default_factory=list)
    console_errors: list[str] = Field(default_factory=list)


class WorkflowFinding(BaseModel):
    workflow_id: str
    persona: str
    runner: Literal["codex", "claude"]
    iterations_used: int
    cost_usd: float = 0.0
    wall_seconds: float
    verdict: Verdict
    severity: Severity | None = None
    summary: str
    repro_steps: list[str] = Field(default_factory=list)
    suggested_regression_check: str | None = None
    evidence: Evidence = Field(default_factory=Evidence)
    notes: str = ""


class RunFinding(BaseModel):
    """Top-level run aggregate written to runs/<ts>/findings.json."""
    app: str
    run_ts: str
    runner: Literal["codex", "claude"]
    budget_usd: float
    cost_usd: float
    wall_seconds: float
    workflows_tested: int
    workflows_skipped: int
    counts: dict[Verdict, int]
    workflow_findings: list[WorkflowFinding]
