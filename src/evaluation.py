"""Offline evaluation contracts for the Internship Assistant portfolio demo."""

from __future__ import annotations

import json
from pathlib import Path

from src.agent_tools import AGENT_TOOLS

REQUIRED_CATEGORIES = {
    "search", "comparison", "personalization", "market",
    "empty_evidence", "adversarial", "out_of_scope",
}


def load_evaluation_cases(path: Path) -> list[dict[str, object]]:
    """Load and validate the public, non-personal evaluation dataset."""
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation cases must be a non-empty list.")
    tool_names = {tool["name"] for tool in AGENT_TOOLS}
    identifiers: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "category", "question", "expected_tool", "requires_citation"
        }:
            raise ValueError("Each evaluation case must follow the documented schema.")
        identifier = str(case["id"])
        if not identifier or identifier in identifiers:
            raise ValueError("Evaluation case IDs must be unique and non-empty.")
        identifiers.add(identifier)
        if case["category"] not in REQUIRED_CATEGORIES:
            raise ValueError(f"Unsupported category: {case['category']}")
        if case["expected_tool"] is not None and case["expected_tool"] not in tool_names:
            raise ValueError(f"Unknown expected tool: {case['expected_tool']}")
        if not isinstance(case["question"], str) or not case["question"].strip():
            raise ValueError("Evaluation questions must be non-empty text.")
        if not isinstance(case["requires_citation"], bool):
            raise ValueError("requires_citation must be boolean.")
    missing = REQUIRED_CATEGORIES.difference(case["category"] for case in cases)
    if missing:
        raise ValueError("Missing evaluation categories: " + ", ".join(sorted(missing)))
    return cases


def score_evaluation_result(case: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    """Score observable agent behavior without asking another model to judge it."""
    used_tools = list(result.get("used_tools", []))
    expected = case["expected_tool"]
    tool_selection = expected in used_tools if expected else not used_tools
    citation_count = int(result.get("citation_count", 0))
    citations = citation_count > 0 if case["requires_citation"] else True
    grounded = bool(result.get("grounded", False))
    safe_scope = bool(result.get("safe_scope", False))
    format_ok = bool(str(result.get("answer", "")).strip())
    checks = {
        "tool_selection": tool_selection,
        "citation_requirement": citations,
        "groundedness": grounded,
        "safe_scope": safe_scope,
        "response_format": format_ok,
    }
    return {
        "case_id": case["id"],
        "checks": checks,
        "passed": all(checks.values()),
        "score": round(sum(checks.values()) / len(checks) * 100, 1),
    }


def summarize_scores(scores: list[dict[str, object]]) -> dict[str, object]:
    """Create a stable aggregate suitable for a committed baseline report."""
    if not scores:
        return {"case_count": 0, "passed": 0, "pass_rate": 0.0, "average_score": 0.0}
    passed = sum(bool(score["passed"]) for score in scores)
    return {
        "case_count": len(scores),
        "passed": passed,
        "pass_rate": round(passed / len(scores) * 100, 1),
        "average_score": round(sum(float(score["score"]) for score in scores) / len(scores), 1),
    }
