"""Deterministic skill-overlap calculations for internship postings."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import TypedDict

import pandas as pd

from src.extract_skills import SKILL_CATALOG


class SkillGapResult(TypedDict):
    """Stable result contract shared by future UI and batch scoring code."""

    matched_skills: list[str]
    missing_skills: list[str]
    matched_count: int
    required_count: int
    match_percentage: float | None


CANONICAL_SKILLS = {
    skill.casefold(): skill
    for category in SKILL_CATALOG.values()
    for skill in category
}


def normalize_skills(skills: Iterable[object] | None) -> list[str]:
    """Return unique, catalog-backed skill names in deterministic order.

    Unknown, null, and blank values are ignored. Strings are rejected because
    they are ambiguous iterables; callers must split serialized CSV values first.
    """
    if skills is None:
        return []
    if isinstance(skills, (str, bytes)):
        raise TypeError("skills must be a collection of values, not a string")

    normalized: set[str] = set()
    for value in skills:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        key = str(value).strip().casefold()
        if key in CANONICAL_SKILLS:
            normalized.add(CANONICAL_SKILLS[key])
    return sorted(normalized, key=str.casefold)


def calculate_skill_gap(
    job_skills: Iterable[object] | None,
    user_skills: Iterable[object] | None,
) -> SkillGapResult:
    """Compare one posting's detected skills with a user's selected skills.

    The percentage measures catalog skill overlap only. ``None`` distinguishes a
    posting with no detected skills from a genuine zero-percent overlap.
    """
    required = normalize_skills(job_skills)
    selected = set(normalize_skills(user_skills))
    matched = [skill for skill in required if skill in selected]
    missing = [skill for skill in required if skill not in selected]
    required_count = len(required)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "matched_count": len(matched),
        "required_count": required_count,
        "match_percentage": (
            round(len(matched) / required_count * 100, 1)
            if required_count
            else None
        ),
    }


def score_postings(postings: pd.DataFrame, user_skills: Iterable[object] | None) -> pd.DataFrame:
    """Return a scored copy of postings without modifying source data."""
    if "skills_extracted" not in postings.columns:
        raise ValueError("Postings must contain a skills_extracted column")

    scored = postings.copy(deep=True)
    results = scored["skills_extracted"].fillna("").map(
        lambda value: calculate_skill_gap(
            [skill for skill in str(value).split("|") if skill], user_skills
        )
    )
    for field in SkillGapResult.__annotations__:
        scored[field] = results.map(lambda result: result[field])
    return scored


def rank_missing_skills(scored_postings: pd.DataFrame) -> pd.DataFrame:
    """Rank missing skills by the number of visible postings requesting them."""
    required = {"posting_id", "missing_skills"}
    missing = required.difference(scored_postings.columns)
    if missing:
        raise ValueError(f"Scored postings are missing: {', '.join(sorted(missing))}")
    exploded = scored_postings[["posting_id", "missing_skills"]].explode("missing_skills")
    exploded = exploded.loc[exploded["missing_skills"].notna() & exploded["missing_skills"].ne("")]
    if exploded.empty:
        return pd.DataFrame(columns=["skill", "posting_count"])
    return (exploded.groupby("missing_skills")["posting_id"].nunique()
            .sort_values(ascending=False).rename_axis("skill")
            .reset_index(name="posting_count")
            .sort_values(["posting_count", "skill"], ascending=[False, True])
            .reset_index(drop=True))
