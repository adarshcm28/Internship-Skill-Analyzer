"""Extract known skills from cleaned internship descriptions."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path("data/processed/cleaned_postings.csv")
DEFAULT_POSTINGS_OUTPUT = Path("data/processed/postings_with_skills.csv")
DEFAULT_SKILLS_OUTPUT = Path("data/processed/posting_skills.csv")

# Each canonical skill can have several text variations. The cleaned descriptions
# produced by ``clean_text.py`` make these aliases predictable and searchable.
SKILL_CATALOG: dict[str, dict[str, tuple[str, ...]]] = {
    "Programming Languages": {
        "Python": ("python",),
        "R": ("r",),
        "SQL": ("sql",),
    },
    "Data Tools": {
        "Excel": ("excel",),
        "Google Sheets": ("google sheets",),
        "Tableau": ("tableau",),
        "Power BI": ("power bi",),
        "Jupyter": ("jupyter", "jupyter notebook", "jupyter notebooks"),
        "Pandas": ("pandas",),
        "NumPy": ("numpy",),
        "Matplotlib": ("matplotlib",),
        "Plotly": ("plotly",),
        "dbt": ("dbt",),
        "BigQuery": ("bigquery",),
        "Snowflake": ("snowflake",),
        "Databricks": ("databricks",),
        "GIS": ("gis", "arcgis", "qgis"),
    },
    "Machine Learning": {
        "Machine Learning": ("machine learning",),
        "Deep Learning": ("deep learning",),
        "NLP": ("nlp",),
        "Computer Vision": ("computer vision",),
        "Scikit-learn": ("scikit learn",),
        "PyTorch": ("pytorch",),
        "Feature Engineering": ("feature engineering",),
        "Model Evaluation": ("model evaluation", "evaluating models"),
        "Clustering": ("clustering",),
        "Classification": ("classification",),
        "Forecasting": ("forecasting",),
        "MLOps": ("mlops",),
    },
    "Statistics and Math": {
        "Statistics": ("statistics", "statistical analysis", "descriptive statistics"),
        "Probability": ("probability",),
        "A/B Testing": ("ab testing",),
        "Regression": ("regression",),
    },
    "Engineering and Cloud": {
        "Git": ("git", "github"),
        "AWS": ("aws",),
        "ETL": ("etl",),
        "Data Pipelines": ("data pipeline", "data pipelines"),
        "Data Modeling": ("data modeling", "data models"),
        "APIs": ("api", "apis"),
        "Spark": ("spark", "spark sql"),
        "Hive": ("hive", "hive sql"),
        "Data Quality": ("data quality", "data validation"),
    },
    "Soft Skills": {
        "Communication": (
            "communication",
            "communicate",
            "communicating",
            "explaining",
        ),
        "Collaboration": ("collaboration", "collaborating", "collaborative"),
        "Problem Solving": ("problem solving",),
        "Presentation": ("presentation", "presenting", "present insights"),
        "Attention to Detail": ("attention to detail",),
    },
}


def contains_alias(text: str, alias: str) -> bool:
    """Match a phrase without allowing partial-word false positives."""
    pattern = rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])"
    return re.search(pattern, text) is not None


def extract_skills(text: object) -> list[tuple[str, str]]:
    """Return unique ``(skill, category)`` pairs found in one description."""
    if pd.isna(text):
        return []

    normalized = str(text).lower()
    found: list[tuple[str, str]] = []
    for category, skills in SKILL_CATALOG.items():
        for skill, aliases in skills.items():
            if any(contains_alias(normalized, alias) for alias in aliases):
                found.append((skill, category))
    return found


def extract_posting_skills(
    input_path: Path,
    postings_output: Path,
    skills_output: Path,
) -> tuple[int, int]:
    """Extract skills and write both wide and normalized result files."""
    postings = pd.read_csv(input_path, dtype=str)
    if "description_cleaned" not in postings.columns:
        raise ValueError("Input must contain a description_cleaned column")

    postings.insert(0, "posting_id", range(1, len(postings) + 1))
    extracted = postings["description_cleaned"].map(extract_skills)
    postings["skills_extracted"] = extracted.map(
        lambda matches: "|".join(skill for skill, _ in matches)
    )
    postings["skill_categories"] = extracted.map(
        lambda matches: "|".join(dict.fromkeys(category for _, category in matches))
    )
    postings["skill_count"] = extracted.map(len)

    skill_rows = [
        {
            "posting_id": posting_id,
            "job_title": job_title,
            "company": company,
            "skill": skill,
            "category": category,
        }
        for posting_id, job_title, company, matches in zip(
            postings["posting_id"],
            postings["job_title"],
            postings["company"],
            extracted,
        )
        for skill, category in matches
    ]
    posting_skills = pd.DataFrame(
        skill_rows,
        columns=["posting_id", "job_title", "company", "skill", "category"],
    )

    postings_output.parent.mkdir(parents=True, exist_ok=True)
    skills_output.parent.mkdir(parents=True, exist_ok=True)
    postings.to_csv(postings_output, index=False)
    posting_skills.to_csv(skills_output, index=False)
    return len(postings), len(posting_skills)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract skills from cleaned postings.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--postings-output", type=Path, default=DEFAULT_POSTINGS_OUTPUT
    )
    parser.add_argument("--skills-output", type=Path, default=DEFAULT_SKILLS_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    posting_count, match_count = extract_posting_skills(
        args.input, args.postings_output, args.skills_output
    )
    print(f"Analyzed {posting_count} postings")
    print(f"Extracted {match_count} posting-skill matches")
    print(f"Wrote enriched postings to {args.postings_output}")
    print(f"Wrote normalized skills to {args.skills_output}")


if __name__ == "__main__":
    main()
