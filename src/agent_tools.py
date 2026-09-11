"""Read-only function tools available to the Internship Assistant."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from typing import Any, TypedDict

import pandas as pd

from src.skill_gap import calculate_skill_gap, normalize_skills, score_postings

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

SEARCH_INTERNSHIPS_TOOL_NAME = "search_internships"
SEARCH_INTERNSHIPS_TOOL = {
    "type": "function",
    "name": SEARCH_INTERNSHIPS_TOOL_NAME,
    "description": (
        "Search the internships in the current dashboard selection. Use this for "
        "requests to find or filter jobs by company, title, US location, skills, "
        "difficulty, or the user's verified skill overlap."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "company": {"type": ["string", "null"], "description": "Company name text, or null."},
            "job_title": {"type": ["string", "null"], "description": "Job title text, or null."},
            "location": {"type": ["string", "null"], "description": "US location text, or null."},
            "skills": {
                "type": "array", "items": {"type": "string"},
                "description": "Catalog skills that every returned posting must contain.",
            },
            "difficulty": {
                "type": ["string", "null"],
                "enum": ["Beginner-friendly", "Advanced", None],
            },
            "minimum_skill_overlap": {
                "type": ["number", "null"], "minimum": 0, "maximum": 100,
                "description": "Minimum verified catalog-skill overlap, or null.",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
        },
        "required": [
            "company", "job_title", "location", "skills", "difficulty",
            "minimum_skill_overlap", "limit",
        ],
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
    total_matches: int
    returned_count: int
    results: list[dict[str, object]]


def _error(posting_id: str, code: str, message: str) -> AgentToolResult:
    return {
        "ok": False,
        "tool": SKILL_GAP_TOOL_NAME,
        "posting_id": posting_id,
        "error": {"code": code, "message": message},
    }


def _search_error(code: str, message: str) -> AgentToolResult:
    return {
        "ok": False,
        "tool": SEARCH_INTERNSHIPS_TOOL_NAME,
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


def search_internships_tool(
    postings: pd.DataFrame,
    user_skills: Iterable[object] | None,
    *,
    company: object = None,
    job_title: object = None,
    location: object = None,
    skills: object = None,
    difficulty: object = None,
    minimum_skill_overlap: object = None,
    limit: object = 5,
) -> AgentToolResult:
    """Search only the supplied dashboard data with validated deterministic filters."""
    required = {"posting_id", "company", "job_title", "location", "skills_extracted"}
    missing = required.difference(postings.columns)
    if missing:
        return _search_error("invalid_dataset", "Required posting data is unavailable.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        return _search_error("invalid_limit", "The result limit must be an integer from 1 to 10.")
    if skills is None:
        skills = []
    if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
        return _search_error("invalid_skills", "Skills must be supplied as a list of catalog skill names.")
    normalized_filters = normalize_skills(skills)
    if len(normalized_filters) != len({skill.strip().casefold() for skill in skills if skill.strip()}):
        return _search_error("unknown_skills", "One or more requested skills are outside the supported catalog.")
    if difficulty not in {None, "Beginner-friendly", "Advanced"}:
        return _search_error("invalid_difficulty", "Difficulty must be Beginner-friendly or Advanced.")
    if minimum_skill_overlap is not None:
        if isinstance(minimum_skill_overlap, bool) or not isinstance(minimum_skill_overlap, (int, float)):
            return _search_error("invalid_overlap", "Minimum skill overlap must be between 0 and 100.")
        if not 0 <= float(minimum_skill_overlap) <= 100:
            return _search_error("invalid_overlap", "Minimum skill overlap must be between 0 and 100.")
        normalized_user, unknown_user = _validated_user_skills(user_skills)
        if unknown_user or not normalized_user:
            return _search_error("no_user_skills", "Select at least one supported skill before filtering by overlap.")

    result = score_postings(postings, user_skills)
    text_filters = (("company", company), ("job_title", job_title), ("location", location))
    for column, value in text_filters:
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            return _search_error("invalid_filter", f"{column} must be non-empty text or null.")
        result = result.loc[result[column].astype(str).str.contains(value.strip(), case=False, na=False, regex=False)]
    if normalized_filters:
        result = result.loc[result["skills_extracted"].fillna("").map(
            lambda value: set(normalize_skills(str(value).split("|"))).issuperset(normalized_filters)
        )]
    if difficulty is not None:
        if "experience_level" not in result.columns:
            return _search_error("invalid_dataset", "Difficulty data is unavailable.")
        result = result.loc[result["experience_level"].eq(difficulty)]
    if minimum_skill_overlap is not None:
        result = result.loc[result["match_percentage"].notna()
                            & result["match_percentage"].ge(float(minimum_skill_overlap))]

    result = result.sort_values(
        ["match_percentage", "company", "job_title"],
        ascending=[False, True, True], na_position="last",
    )
    total = len(result)
    rows: list[dict[str, object]] = []
    for _, row in result.head(limit).iterrows():
        source_url = str(row.get("source_url", "") or "")
        if source_url and not source_url.startswith(("https://", "http://")):
            source_url = ""
        rows.append({
            "posting_id": str(row["posting_id"]),
            "company": str(row["company"]),
            "job_title": str(row["job_title"]),
            "location": str(row["location"]),
            "difficulty": str(row.get("experience_level", "") or ""),
            "skills": normalize_skills(str(row.get("skills_extracted", "") or "").split("|")),
            "match_percentage": None if pd.isna(row["match_percentage"]) else float(row["match_percentage"]),
            "matched_skills": row["matched_skills"],
            "missing_skills": row["missing_skills"],
            "source_url": source_url,
        })
    return {
        "ok": True,
        "tool": SEARCH_INTERNSHIPS_TOOL_NAME,
        "total_matches": total,
        "returned_count": len(rows),
        "results": rows,
    }


def dispatch_tool_call(
    name: str,
    arguments: str,
    postings: pd.DataFrame,
    user_skills: Iterable[object] | None,
) -> AgentToolResult:
    """Validate and execute an allowlisted tool call without raising to the UI."""
    if name not in {SKILL_GAP_TOOL_NAME, SEARCH_INTERNSHIPS_TOOL_NAME}:
        return _error("", "unknown_tool", "The requested tool is not available.")
    try:
        parsed: Any = json.loads(arguments)
    except (json.JSONDecodeError, TypeError):
        return _error("", "invalid_arguments", "Tool arguments must be valid JSON.")
    if not isinstance(parsed, dict):
        return _error("", "invalid_arguments", "Tool arguments must be a JSON object.")
    if name == SKILL_GAP_TOOL_NAME:
        if set(parsed) != {"posting_id"}:
            return _error("", "invalid_arguments", "The tool requires only a posting_id.")
        return analyze_skill_gap_tool(postings, parsed["posting_id"], user_skills)
    expected = {
        "company", "job_title", "location", "skills", "difficulty",
        "minimum_skill_overlap", "limit",
    }
    if set(parsed) != expected:
        return _search_error("invalid_arguments", "The search tool requires its complete filter schema.")
    return search_internships_tool(postings, user_skills, **parsed)
