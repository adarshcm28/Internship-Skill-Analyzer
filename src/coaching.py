"""Helpers for starting job-specific coaching conversations."""

from __future__ import annotations

from collections.abc import Mapping


def build_coaching_question(posting: Mapping[str, object]) -> str:
    """Create a bounded request tied to one stable posting identifier."""
    posting_id = str(posting.get("posting_id", "") or "").strip()
    company = str(posting.get("company", "") or "").strip()
    title = str(posting.get("job_title", "") or "").strip()
    return (
        f"Help me prepare for posting {posting_id}: {title} at {company}. "
        "Use the verified skill-gap tool for this posting. Give me preparation steps, "
        "explain my missing skills, suggest questions I should research before applying, "
        "and cite the original posting source."
    )[:2000]
