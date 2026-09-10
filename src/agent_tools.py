"""Read-only function tools available to the Internship Assistant."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from typing import Any, TypedDict

import pandas as pd

from src.skill_gap import calculate_skill_gap, normalize_skills

SKILL_GAP_TOOL_NAME = "analyze_skill_gap"
SKILL_GAP_TOOL = {
    "type": "function",
    "name": SKILL_GAP_TOOL_NAME,
    "description": (
        "Calculate the current user's verified skill overlap for one visible "
        "internship. Use this when the user asks why a specific posting matches, "
        "what skills they have, or what skills they are missing."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "posting_id": {
                "type": "string",
                "description": "Exact citation_id/posting_id from the supplied posting evidence.",
            },
        },
        "required": ["posting_id"],
        "additionalProperties": False,
    },
}


class AgentToolResult(TypedDict, total=False):
    """Serializable result contract for all outcomes of this milestone's tool."""

    ok: bool
    tool: str
    posting_id: str
    company: str
    job_title: str
    calculation: dict[str, object]
    error: dict[str, str]


def _error(posting_id: str, code: str, message: str) -> AgentToolResult:
    return {
        "ok": False,
        "tool": SKILL_GAP_TOOL_NAME,
        "posting_id": posting_id,
        "error": {"code": code, "message": message},
    }


def _validated_user_skills(skills: Iterable[object] | None) -> tuple[list[str], list[str]]:
    values = [] if skills is None else list(skills)
    normalized = normalize_skills(values)
    known = {skill.casefold() for skill in normalized}
    unknown = sorted({
        str(value).strip()
        for value in values
        if value is not None
        and not (isinstance(value, float) and math.isnan(value))
        and str(value).strip()
        and str(value).strip().casefold() not in known
    }, key=str.casefold)
    return normalized, unknown


def analyze_skill_gap_tool(
    postings: pd.DataFrame,
    posting_id: object,
    user_skills: Iterable[object] | None,
) -> AgentToolResult:
    """Calculate one posting's skill gap using trusted application state."""
    identifier = str(posting_id or "").strip()
    if not identifier:
        return _error("", "invalid_posting_id", "A non-empty posting ID is required.")
    if "posting_id" not in postings.columns or "skills_extracted" not in postings.columns:
        return _error(identifier, "invalid_dataset", "Required posting data is unavailable.")

    normalized_skills, unknown = _validated_user_skills(user_skills)
    if unknown:
        return _error(
            identifier,
            "unknown_user_skills",
            "The current profile contains skills outside the supported catalog: " + ", ".join(unknown),
        )
    if not normalized_skills:
        return _error(
            identifier,
            "no_user_skills",
            "Select at least one skill under My Skills before requesting a skill-gap analysis.",
        )

    matching = postings.loc[postings["posting_id"].astype(str).eq(identifier)]
    if matching.empty:
        return _error(identifier, "posting_not_found", "That posting is not in the current dashboard selection.")
    if len(matching) > 1:
        return _error(identifier, "duplicate_posting_id", "That posting ID is not unique in the current selection.")

    row = matching.iloc[0]
    job_skills = [skill for skill in str(row.get("skills_extracted", "") or "").split("|") if skill]
    calculation = calculate_skill_gap(job_skills, normalized_skills)
    return {
        "ok": True,
        "tool": SKILL_GAP_TOOL_NAME,
        "posting_id": identifier,
        "company": str(row.get("company", "") or ""),
        "job_title": str(row.get("job_title", "") or ""),
        "calculation": {
            **calculation,
            "selected_skills": normalized_skills,
            "calculation_method": "deterministic_catalog_skill_overlap",
            "interpretation": "Navigation aid only; not an eligibility or hiring prediction.",
        },
    }


def dispatch_tool_call(
    name: str,
    arguments: str,
    postings: pd.DataFrame,
    user_skills: Iterable[object] | None,
) -> AgentToolResult:
    """Validate and execute an allowlisted tool call without raising to the UI."""
    if name != SKILL_GAP_TOOL_NAME:
        return _error("", "unknown_tool", "The requested tool is not available.")
    try:
        parsed: Any = json.loads(arguments)
    except (json.JSONDecodeError, TypeError):
        return _error("", "invalid_arguments", "Tool arguments must be valid JSON.")
    if not isinstance(parsed, dict) or set(parsed) != {"posting_id"}:
        return _error("", "invalid_arguments", "The tool requires only a posting_id.")
    return analyze_skill_gap_tool(postings, parsed["posting_id"], user_skills)
