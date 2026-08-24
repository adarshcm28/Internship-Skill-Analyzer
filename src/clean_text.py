"""Clean raw internship descriptions for repeatable skill analysis."""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path("data/raw/internship_postings.csv")
DEFAULT_OUTPUT = Path("data/processed/cleaned_postings.csv")
REQUIRED_COLUMNS = {
    "job_title",
    "company",
    "location",
    "description",
    "source",
    "date_collected",
}

# Variations are converted to one searchable spelling before punctuation removal.
TERM_PATTERNS = {
    r"\bpower[\s_-]*bi\b": "power bi",
    r"\bscikit[\s_-]*learn\b": "scikit learn",
    r"\bmachine[\s_-]*learning\b": "machine learning",
    r"\bdeep[\s_-]*learning\b": "deep learning",
    r"\ba\s*/\s*b\s+testing\b": "ab testing",
    r"\bnatural[\s_-]*language[\s_-]*processing\b": "nlp",
}


def clean_description(value: object) -> str:
    """Return normalized text suitable for keyword-based skill extraction."""
    if pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKC", html.unescape(str(value))).lower()
    text = text.replace("&", " and ")

    for pattern, replacement in TERM_PATTERNS.items():
        text = re.sub(pattern, replacement, text)

    # Keep + and # so skills such as C++ and C# remain distinguishable.
    text = re.sub(r"[^a-z0-9+#\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_postings(input_path: Path, output_path: Path) -> tuple[int, int]:
    """Clean a raw CSV, write valid rows, and return kept/dropped counts."""
    postings = pd.read_csv(input_path, dtype=str)
    missing_columns = REQUIRED_COLUMNS.difference(postings.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    postings["description_cleaned"] = postings["description"].map(clean_description)
    empty_descriptions = postings["description_cleaned"].eq("")
    dropped_count = int(empty_descriptions.sum())
    cleaned = postings.loc[~empty_descriptions].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False)
    return len(cleaned), dropped_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean internship posting descriptions."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    kept, dropped = clean_postings(args.input, args.output)
    print(f"Wrote {kept} cleaned postings to {args.output}")
    print(f"Dropped {dropped} rows with empty descriptions")


if __name__ == "__main__":
    main()
