"""Verified user-profile context for the Internship Assistant."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Literal, TypedDict

import pandas as pd

from src.skill_gap import normalize_skills, score_postings


class UserSkillProfile(TypedDict):
    """A small profile that exists only for the current app session."""

    status: Literal["active", "no_skills_selected"]
    selected_skills: list[str]
    ignored_unknown_skills: list[str]
    selected_skill_count: int
    persistence: Literal["current_session_only"]


def build_user_profile(skills: Iterable[object] | None) -> UserSkillProfile:
    """Normalize selected skills while making ignored values explicit."""
    values = [] if skills is None else list(skills)
    selected = normalize_skills(values)
    selected_keys = {skill.casefold() for skill in selected}
    ignored = sorted({
        str(value).strip()
        for value in values
        if value is not None
        and not (isinstance(value, float) and pd.isna(value))
        and str(value).strip()
        and str(value).strip().casefold() not in selected_keys
    }, key=str.casefold)
    return {
        "status": "active" if selected else "no_skills_selected",
        "selected_skills": selected,
        "ignored_unknown_skills": ignored,
        "selected_skill_count": len(selected),
        "persistence": "current_session_only",
    }


def build_personalization_context(
    postings: pd.DataFrame,
    skills: Iterable[object] | None,
) -> str:
    """Serialize the profile and deterministic match summary for model context."""
    profile = build_user_profile(skills)
    summary: dict[str, object] = {
        "status": "not_calculated",
        "visible_postings": len(postings),
        "scored_postings": 0,
        "average_match_percentage": None,
        "best_match_percentage": None,
    }
    if profile["status"] == "active":
        scored = score_postings(postings, profile["selected_skills"])
        percentages = scored["match_percentage"].dropna()
        summary = {
            "status": "calculated_by_application",
            "visible_postings": len(scored),
            "scored_postings": len(percentages),
            "average_match_percentage": (
                round(float(percentages.mean()), 1) if not percentages.empty else None
            ),
            "best_match_percentage": (
                round(float(percentages.max()), 1) if not percentages.empty else None
            ),
        }
    return json.dumps({
        "profile": profile,
        "match_summary": summary,
        "interpretation": (
            "Match values are deterministic catalog-skill overlap calculations, "
            "not eligibility, interview, or hiring predictions."
        ),
    }, ensure_ascii=False)


def profile_fingerprint(skills: Iterable[object] | None) -> str:
    """Identify profile changes without persisting a profile outside the session."""
    profile = build_user_profile(skills)
    return hashlib.sha256(
        json.dumps(profile["selected_skills"], sort_keys=True).encode()
    ).hexdigest()
