"""Collect current data-related internships from public company job-board APIs.

The collector uses the public JSON endpoints provided by Ashby and Lever. It
does not submit applications, access private postings, or scrape arbitrary HTML.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import pandas as pd
import requests


DEFAULT_CONFIG = Path("config/job_boards.json")
DEFAULT_OUTPUT = Path("data/raw/internship_postings.csv")
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "Internship-Skill-Analyzer/1.0 (educational project)"

DATA_ROLE_PATTERN = re.compile(
    r"\b(data|analytics?|machine learning|artificial intelligence|ai|"
    r"business intelligence|applied scientist|research scientist)\b",
    re.IGNORECASE,
)
EARLY_CAREER_PATTERN = re.compile(
    r"\b(intern|internship|co[ -]?op|graduate)\b", re.IGNORECASE
)
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class JobBoard:
    company: str
    provider: str
    board: str


@dataclass(frozen=True)
class Posting:
    job_title: str
    company: str
    location: str
    description: str
    source: str
    source_url: str
    date_collected: str
    provider: str
    external_posting_id: str
    published_at: str
    employment_type: str
    workplace_type: str


class _HTMLTextExtractor(HTMLParser):
    """Collect readable text from the small HTML fragments returned by Lever."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: object) -> str:
    """Convert API-provided HTML fragments to normalized plain text."""
    parser = _HTMLTextExtractor()
    parser.feed(html.unescape(str(value or "")))
    return normalize_text(" ".join(parser.parts))


def normalize_text(value: object) -> str:
    """Collapse newlines and repeated spaces while preserving source wording."""
    return WHITESPACE_PATTERN.sub(" ", str(value or "")).strip()


def load_boards(config_path: Path) -> list[JobBoard]:
    """Read and validate the company job-board configuration."""
    raw_boards = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw_boards, list) or not raw_boards:
        raise ValueError("Job-board configuration must be a non-empty JSON list")

    boards: list[JobBoard] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_boards:
        board = JobBoard(
            company=normalize_text(item.get("company")),
            provider=normalize_text(item.get("provider")).lower(),
            board=normalize_text(item.get("board")),
        )
        if not all((board.company, board.provider, board.board)):
            raise ValueError(f"Incomplete job-board entry: {item}")
        if board.provider not in {"ashby", "lever"}:
            raise ValueError(f"Unsupported provider: {board.provider}")
        key = (board.provider, board.board)
        if key in seen:
            raise ValueError(f"Duplicate job board: {board.provider}/{board.board}")
        seen.add(key)
        boards.append(board)
    return boards


def is_target_posting(title: str, description: str, employment_type: str) -> bool:
    """Keep data-related roles that are explicitly early-career or internships."""
    if not DATA_ROLE_PATTERN.search(title):
        return False
    early_career_text = f"{title} {description[:2500]}"
    return (
        employment_type.lower() == "intern"
        or EARLY_CAREER_PATTERN.search(early_career_text) is not None
    )


def fetch_json(session: requests.Session, url: str) -> Any:
    """Fetch one public JSON endpoint with a finite timeout."""
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def collect_ashby(
    board: JobBoard, session: requests.Session, collected_on: str
) -> list[Posting]:
    """Collect listed jobs from an Ashby public job board."""
    endpoint = f"https://api.ashbyhq.com/posting-api/job-board/{board.board}"
    payload = fetch_json(session, endpoint)
    postings: list[Posting] = []

    for job in payload.get("jobs", []):
        if not job.get("isListed", True):
            continue
        title = normalize_text(job.get("title"))
        description = normalize_text(job.get("descriptionPlain"))
        employment_type = normalize_text(job.get("employmentType"))
        if not is_target_posting(title, description, employment_type):
            continue

        source_url = normalize_text(job.get("jobUrl"))
        external_id = urlparse(source_url).path.rstrip("/").split("/")[-1]
        postings.append(
            Posting(
                job_title=title,
                company=board.company,
                location=normalize_text(job.get("location")) or "Not specified",
                description=description,
                source="Ashby public Job Postings API",
                source_url=source_url,
                date_collected=collected_on,
                provider="ashby",
                external_posting_id=external_id,
                published_at=normalize_text(job.get("publishedAt")),
                employment_type=employment_type,
                workplace_type=normalize_text(job.get("workplaceType")),
            )
        )
    return postings


def collect_lever(
    board: JobBoard, session: requests.Session, collected_on: str
) -> list[Posting]:
    """Collect published jobs from a Lever public postings site."""
    endpoint = f"https://api.lever.co/v0/postings/{board.board}?mode=json"
    jobs = fetch_json(session, endpoint)
    postings: list[Posting] = []

    for job in jobs:
        title = normalize_text(job.get("text"))
        list_sections = [
            " ".join(
                part
                for part in (
                    normalize_text(section.get("text")),
                    html_to_text(section.get("content")),
                )
                if part
            )
            for section in (job.get("lists") or [])
        ]
        description = normalize_text(
            " ".join(
                part
                for part in (
                    job.get("descriptionPlain"),
                    *list_sections,
                    job.get("additionalPlain"),
                )
                if part
            )
        )
        categories = job.get("categories") or {}
        employment_type = normalize_text(categories.get("commitment"))
        if not is_target_posting(title, description, employment_type):
            continue

        postings.append(
            Posting(
                job_title=title,
                company=board.company,
                location=normalize_text(categories.get("location")) or "Not specified",
                description=description,
                source="Lever public Postings API",
                source_url=normalize_text(job.get("hostedUrl")),
                date_collected=collected_on,
                provider="lever",
                external_posting_id=normalize_text(job.get("id")),
                published_at="",
                employment_type=employment_type,
                workplace_type=normalize_text(job.get("workplaceType")),
            )
        )
    return postings


def collect_from_boards(
    boards: Iterable[JobBoard], collected_on: str
) -> tuple[list[Posting], list[str]]:
    """Query every configured board, continuing past individual board errors."""
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "User-Agent": USER_AGENT})
    postings: list[Posting] = []
    errors: list[str] = []

    for board in boards:
        try:
            if board.provider == "ashby":
                found = collect_ashby(board, session, collected_on)
            else:
                found = collect_lever(board, session, collected_on)
            postings.extend(found)
            print(f"{board.company}: found {len(found)} matching posting(s)")
        except (requests.RequestException, ValueError, TypeError) as exc:
            message = f"{board.company} ({board.provider}/{board.board}): {exc}"
            errors.append(message)
            print(f"Warning: {message}", file=sys.stderr)
    return postings, errors


def postings_frame(postings: Iterable[Posting]) -> pd.DataFrame:
    """Create a deterministic, deduplicated dataframe for the raw CSV."""
    columns = list(Posting.__dataclass_fields__)
    frame = pd.DataFrame((asdict(posting) for posting in postings), columns=columns)
    if frame.empty:
        return frame

    frame = frame.loc[
        frame["job_title"].ne("")
        & frame["company"].ne("")
        & frame["description"].ne("")
        & frame["source_url"].str.startswith("https://")
    ].copy()
    frame = frame.drop_duplicates(subset=["source_url"], keep="first")
    return frame.sort_values(
        ["company", "job_title", "source_url"], key=lambda values: values.str.lower()
    ).reset_index(drop=True)


def write_postings(frame: pd.DataFrame, output_path: Path) -> None:
    """Write through a temporary file so failed collections keep old data safe."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".csv.tmp")
    frame.to_csv(temporary_path, index=False)
    temporary_path.replace(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect current data internships from public job-board APIs."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--minimum-postings",
        type=int,
        default=5,
        help="Do not replace the CSV unless at least this many matches are found.",
    )
    parser.add_argument(
        "--collected-on",
        default=date.today().isoformat(),
        help="Collection date written to the CSV (default: today).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate data without replacing the raw CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.minimum_postings < 1:
        raise ValueError("--minimum-postings must be at least 1")

    boards = load_boards(args.config)
    postings, errors = collect_from_boards(boards, args.collected_on)
    frame = postings_frame(postings)
    if len(frame) < args.minimum_postings:
        raise RuntimeError(
            f"Found {len(frame)} valid postings; minimum is {args.minimum_postings}. "
            "The existing raw CSV was not replaced."
        )

    if args.dry_run:
        print(f"Dry run passed with {len(frame)} valid posting(s); no file was written")
    else:
        write_postings(frame, args.output)
        print(f"Wrote {len(frame)} current posting(s) to {args.output}")
    if errors:
        print(f"Completed with {len(errors)} board warning(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
