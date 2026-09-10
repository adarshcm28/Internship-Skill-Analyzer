"""Deterministic retrieval for grounding Internship Assistant responses."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

import pandas as pd

DEFAULT_MAX_POSTINGS = 12
DEFAULT_DESCRIPTION_CHARS = 700
DEFAULT_CONTEXT_CHARS = 24_000

CONTEXT_COLUMNS = [
    "posting_id", "company", "job_title", "location", "skills_extracted",
    "experience_level", "source_url", "date_collected", "description",
    "match_percentage", "matched_skills", "missing_skills", "matched_count",
    "required_count",
]
FIELD_WEIGHTS = {
    "job_title": 5,
    "skills_extracted": 4,
    "company": 3,
    "location": 2,
    "description": 1,
}
STOP_WORDS = {
    "about", "and", "are", "can", "does", "for", "from", "have", "internship",
    "internships", "job", "jobs", "mention", "show", "that", "the", "these", "this",
    "what", "which", "with", "would", "you",
}


def query_terms(question: str) -> list[str]:
    """Return unique, meaningful lowercase terms in their original order."""
    terms: list[str] = []
    for token in re.findall(r"[a-z0-9][a-z0-9+#.\-]*", question.lower()):
        if len(token) < 2 or token in STOP_WORDS or token in terms:
            continue
        terms.append(token)
    return terms[:20]


def _safe_url(value: Any) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    return url if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _stable_id(row: pd.Series) -> str:
    supplied = str(row.get("posting_id", "") or "").strip()
    if supplied:
        return supplied
    identity = "|".join(
        str(row.get(column, "") or "").strip().lower()
        for column in ("company", "job_title", "location", "source_url")
    )
    return "posting-" + hashlib.sha256(identity.encode()).hexdigest()[:10]


def _search_score(row: pd.Series, terms: list[str]) -> int:
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        value = str(row.get(field, "") or "").lower()
        score += sum(weight for term in terms if term in value)
    return score


def rank_postings(frame: pd.DataFrame, question: str) -> pd.DataFrame:
    """Return unique postings ordered by lexical relevance and original order."""
    rows = frame.reindex(columns=CONTEXT_COLUMNS).fillna("").copy()
    rows["citation_id"] = rows.apply(_stable_id, axis=1)
    rows["source_url"] = rows["source_url"].map(_safe_url)
    rows = rows.drop_duplicates(subset="citation_id", keep="first")
    terms = query_terms(question)
    rows["retrieval_score"] = rows.apply(_search_score, axis=1, terms=terms)
    rows["_original_order"] = range(len(rows))
    return rows.sort_values(
        ["retrieval_score", "_original_order"], ascending=[False, True], kind="stable"
    ).drop(columns="_original_order")


def _selection_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame:
        return {}
    values = frame[column].fillna("").astype(str).str.strip()
    return values.loc[values.ne("")].value_counts().to_dict()


def build_retrieval_context(
    frame: pd.DataFrame,
    question: str,
    *,
    max_postings: int = DEFAULT_MAX_POSTINGS,
    description_chars: int = DEFAULT_DESCRIPTION_CHARS,
    max_context_chars: int = DEFAULT_CONTEXT_CHARS,
) -> str:
    """Build valid, bounded JSON evidence for one user question."""
    if max_postings < 1 or description_chars < 0 or max_context_chars < 1_000:
        raise ValueError("Context limits must be positive and max_context_chars at least 1000")

    terms = query_terms(question)
    ranked = rank_postings(frame, question)
    relevant = ranked.loc[ranked["retrieval_score"].gt(0)]
    strategy = "lexical_relevance"
    candidates = relevant
    if relevant.empty:
        strategy = "representative_fallback"
        candidates = ranked

    context: dict[str, Any] = {
        "scope": "Current dashboard selection",
        "total_postings": len(frame),
        "unique_postings": len(ranked),
        "company_counts": _selection_counts(frame, "company"),
        "difficulty_counts": _selection_counts(frame, "experience_level"),
        "retrieval": {
            "question_terms": terms,
            "strategy": strategy,
            "matching_postings": len(relevant),
            "maximum_postings": max_postings,
            "maximum_context_characters": max_context_chars,
        },
        "citation_format": "Cite a posting as [citation_id](source_url). Omit the link if source_url is empty.",
        "description_note": f"Descriptions are excerpts of at most {description_chars} characters.",
        "postings": [],
    }

    output_columns = ["citation_id", *CONTEXT_COLUMNS[1:], "retrieval_score"]
    for _, row in candidates.head(max_postings).iterrows():
        posting = row.reindex(output_columns).to_dict()
        posting["description"] = str(posting["description"])[:description_chars]
        context["postings"].append(posting)
        encoded = json.dumps(context, ensure_ascii=False, default=str)
        if len(encoded) > max_context_chars:
            context["postings"].pop()
            break

    context["retrieval"]["included_postings"] = len(context["postings"])
    return json.dumps(context, ensure_ascii=False, default=str)


def selection_fingerprint(frame: pd.DataFrame) -> str:
    """Identify a filtered selection without serializing descriptions or secrets."""
    rows = frame.reindex(columns=["posting_id", "source_url"]).fillna("")
    identifiers = sorted("|".join(map(str, row)) for row in rows.itertuples(index=False, name=None))
    return hashlib.sha256(json.dumps(identifiers).encode()).hexdigest()
