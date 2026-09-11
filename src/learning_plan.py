"""Structured, evidence-based learning plans for the current skill profile."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, Callable, TypedDict

import pandas as pd
from openai import OpenAI

from src.skill_gap import rank_missing_skills

TIMEFRAME_OPTIONS = (2, 4, 8, 12)

LEARNING_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "timeframe_weeks": {"type": "integer"},
        "data_backed_priorities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "posting_count": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["skill", "posting_count", "reason"],
                "additionalProperties": False,
            },
        },
        "weekly_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "week_start": {"type": "integer"},
                    "week_end": {"type": "integer"},
                    "focus": {"type": "string"},
                    "practice_task": {"type": "string"},
                },
                "required": ["week_start", "week_end", "focus", "practice_task"],
                "additionalProperties": False,
            },
        },
        "portfolio_project": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "skills_practiced": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "description", "skills_practiced"],
            "additionalProperties": False,
        },
        "general_guidance": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "string"},
    },
    "required": [
        "title", "timeframe_weeks", "data_backed_priorities", "weekly_steps",
        "portfolio_project", "general_guidance", "limitations",
    ],
    "additionalProperties": False,
}


class LearningPlan(TypedDict):
    title: str
    timeframe_weeks: int
    data_backed_priorities: list[dict[str, object]]
    weekly_steps: list[dict[str, object]]
    portfolio_project: dict[str, object]
    general_guidance: list[str]
    limitations: str


def build_learning_plan_evidence(
    scored_postings: pd.DataFrame,
    user_skills: Iterable[str],
    timeframe_weeks: int,
) -> dict[str, object]:
    """Create the only facts the model may use to prioritize a plan."""
    if timeframe_weeks not in TIMEFRAME_OPTIONS:
        raise ValueError(f"Timeframe must be one of: {', '.join(map(str, TIMEFRAME_OPTIONS))}")
    priorities = rank_missing_skills(scored_postings).head(5).to_dict("records")
    return {
        "timeframe_weeks": timeframe_weeks,
        "selected_skills": sorted(set(user_skills), key=str.casefold),
        "visible_posting_count": len(scored_postings),
        "missing_skill_frequencies": priorities,
        "priority_source": "deterministic counts from the current dashboard selection",
    }


def parse_learning_plan(raw: str, timeframe_weeks: int) -> LearningPlan | None:
    """Reject malformed model output before it reaches the dashboard."""
    try:
        value: Any = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    required = set(LEARNING_PLAN_SCHEMA["required"])
    if not isinstance(value, dict) or set(value) != required:
        return None
    if value.get("timeframe_weeks") != timeframe_weeks:
        return None
    if not isinstance(value.get("data_backed_priorities"), list):
        return None
    if not isinstance(value.get("weekly_steps"), list):
        return None
    if not isinstance(value.get("portfolio_project"), dict):
        return None
    if not isinstance(value.get("general_guidance"), list):
        return None
    return value


def fallback_learning_plan(evidence: dict[str, object]) -> LearningPlan:
    """Provide a useful deterministic plan if structured model output is invalid."""
    weeks = int(evidence["timeframe_weeks"])
    priorities = list(evidence["missing_skill_frequencies"])
    data_priorities = [
        {
            "skill": str(item["skill"]),
            "posting_count": int(item["posting_count"]),
            "reason": f"Detected in {int(item['posting_count'])} visible posting(s).",
        }
        for item in priorities
    ]
    focus = ", ".join(item["skill"] for item in data_priorities[:3]) or "your existing skills"
    return {
        "title": f"{weeks}-week internship skills plan",
        "timeframe_weeks": weeks,
        "data_backed_priorities": data_priorities,
        "weekly_steps": [{
            "week_start": 1,
            "week_end": weeks,
            "focus": focus,
            "practice_task": "Build one small, documented project and record what you learned each week.",
        }],
        "portfolio_project": {
            "title": "Internship-ready data project",
            "description": "Use a public dataset to demonstrate the highest-priority skills and explain your decisions.",
            "skills_practiced": [item["skill"] for item in data_priorities[:3]],
        },
        "general_guidance": ["Adjust the pace to your experience and available time."],
        "limitations": "This plan is guidance based on catalog skills in the visible postings; it does not guarantee readiness, interviews, or hiring.",
    }


def generate_learning_plan(
    key: str,
    model: str,
    evidence: dict[str, object],
    client_factory: Callable[..., OpenAI] = OpenAI,
) -> tuple[LearningPlan, bool]:
    """Generate a strict JSON plan, returning a safe fallback when validation fails."""
    weeks = int(evidence["timeframe_weeks"])
    instructions = (
        "Create a concise internship-skills learning plan using only the supplied JSON facts. "
        "Keep data_backed_priorities faithful to missing_skill_frequencies and place broader "
        "advice only in general_guidance. Do not promise readiness, interviews, or hiring."
    )
    with client_factory(api_key=key, timeout=30.0, max_retries=1) as client:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=json.dumps(evidence, ensure_ascii=False),
            text={"format": {
                "type": "json_schema",
                "name": "personalized_learning_plan",
                "strict": True,
                "schema": LEARNING_PLAN_SCHEMA,
            }},
            max_output_tokens=2200,
            store=False,
        )
    parsed = parse_learning_plan(response.output_text, weeks)
    return (parsed, False) if parsed is not None else (fallback_learning_plan(evidence), True)
