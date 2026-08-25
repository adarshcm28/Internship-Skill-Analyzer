"""Analyze skill demand across processed internship postings."""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import pandas as pd


DEFAULT_POSTINGS = Path("data/processed/postings_with_skills.csv")
DEFAULT_SKILLS = Path("data/processed/posting_skills.csv")
DEFAULT_OUTPUT_DIR = Path("data/processed/analysis")

# A posting is labeled advanced when it mentions at least two skills from this
# set. This is a simple, explainable heuristic—not an employability judgment.
ADVANCED_SKILLS = {
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Computer Vision",
    "Scikit-learn",
    "PyTorch",
    "Feature Engineering",
    "Model Evaluation",
    "Clustering",
    "Classification",
    "Forecasting",
    "MLOps",
    "AWS",
    "ETL",
    "Spark",
    "Hive",
}
ADVANCED_THRESHOLD = 2


def validate_inputs(postings: pd.DataFrame, skills: pd.DataFrame) -> None:
    required_posting_columns = {"posting_id", "job_title", "company"}
    required_skill_columns = {"posting_id", "skill", "category"}
    missing_postings = required_posting_columns.difference(postings.columns)
    missing_skills = required_skill_columns.difference(skills.columns)
    if missing_postings:
        raise ValueError(
            f"Postings file is missing: {', '.join(sorted(missing_postings))}"
        )
    if missing_skills:
        raise ValueError(
            f"Skills file is missing: {', '.join(sorted(missing_skills))}"
        )


def build_skill_summary(skills: pd.DataFrame, total_postings: int) -> pd.DataFrame:
    """Count the number and percentage of postings mentioning each skill."""
    summary = (
        skills.groupby(["skill", "category"], as_index=False)["posting_id"]
        .nunique()
        .rename(columns={"posting_id": "posting_count"})
        .sort_values(["posting_count", "skill"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary.insert(0, "rank", range(1, len(summary) + 1))
    summary["percentage"] = (summary["posting_count"] / total_postings * 100).round(1)
    return summary


def build_category_summary(skills: pd.DataFrame, total_postings: int) -> pd.DataFrame:
    """Summarize category reach and total posting-skill mentions."""
    summary = (
        skills.groupby("category")
        .agg(
            posting_count=("posting_id", "nunique"),
            skill_mentions=("skill", "size"),
            unique_skills=("skill", "nunique"),
        )
        .reset_index()
    )
    summary["percentage_of_postings"] = (
        summary["posting_count"] / total_postings * 100
    ).round(1)
    return summary.sort_values(
        ["posting_count", "skill_mentions", "category"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_skill_combinations(
    skills: pd.DataFrame, total_postings: int
) -> pd.DataFrame:
    """Count each unordered pair of skills that appears in the same posting."""
    rows: list[dict[str, object]] = []
    for posting_id, group in skills.groupby("posting_id"):
        posting_skills = sorted(group["skill"].unique())
        rows.extend(
            {"posting_id": posting_id, "skill_1": first, "skill_2": second}
            for first, second in combinations(posting_skills, 2)
        )

    if not rows:
        return pd.DataFrame(
            columns=["skill_1", "skill_2", "posting_count", "percentage"]
        )

    pairs = pd.DataFrame(rows)
    summary = (
        pairs.groupby(["skill_1", "skill_2"], as_index=False)["posting_id"]
        .nunique()
        .rename(columns={"posting_id": "posting_count"})
    )
    summary["percentage"] = (summary["posting_count"] / total_postings * 100).round(1)
    return summary.sort_values(
        ["posting_count", "skill_1", "skill_2"], ascending=[False, True, True]
    ).reset_index(drop=True)


def classify_postings(
    postings: pd.DataFrame, skills: pd.DataFrame
) -> pd.DataFrame:
    """Classify postings using the documented advanced-skill threshold."""
    advanced = skills.loc[skills["skill"].isin(ADVANCED_SKILLS)]
    advanced_by_posting = advanced.groupby("posting_id")["skill"].agg(
        lambda values: "|".join(sorted(values.unique()))
    )

    result = postings[["posting_id", "job_title", "company"]].copy()
    result["advanced_skills"] = result["posting_id"].map(advanced_by_posting).fillna("")
    result["advanced_skill_count"] = result["advanced_skills"].map(
        lambda value: 0 if not value else len(value.split("|"))
    )
    result["experience_level"] = result["advanced_skill_count"].map(
        lambda count: "Advanced" if count >= ADVANCED_THRESHOLD else "Beginner-friendly"
    )
    result["classification_rule"] = (
        f"Advanced when {ADVANCED_THRESHOLD}+ advanced skills are mentioned"
    )
    return result


def analyze(
    postings_path: Path, skills_path: Path, output_dir: Path
) -> dict[str, pd.DataFrame]:
    postings = pd.read_csv(postings_path)
    skills = pd.read_csv(skills_path)
    validate_inputs(postings, skills)

    total_postings = postings["posting_id"].nunique()
    if total_postings == 0:
        raise ValueError("No postings are available for analysis")

    skill_summary = build_skill_summary(skills, total_postings)
    category_summary = build_category_summary(skills, total_postings)
    skill_combinations = build_skill_combinations(skills, total_postings)
    posting_difficulty = classify_postings(postings, skills)

    level_counts = posting_difficulty["experience_level"].value_counts()
    analysis_summary = pd.DataFrame(
        [
            ("total_postings", total_postings),
            ("unique_skills", skills["skill"].nunique()),
            ("posting_skill_matches", len(skills)),
            ("beginner_friendly_postings", int(level_counts.get("Beginner-friendly", 0))),
            ("advanced_postings", int(level_counts.get("Advanced", 0))),
        ],
        columns=["metric", "value"],
    )

    outputs = {
        "analysis_summary.csv": analysis_summary,
        "skill_summary.csv": skill_summary,
        "category_summary.csv": category_summary,
        "skill_combinations.csv": skill_combinations,
        "posting_difficulty.csv": posting_difficulty,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(output_dir / filename, index=False)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze internship skill trends.")
    parser.add_argument("--postings", type=Path, default=DEFAULT_POSTINGS)
    parser.add_argument("--skills", type=Path, default=DEFAULT_SKILLS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = analyze(args.postings, args.skills, args.output_dir)
    summary = outputs["analysis_summary.csv"].set_index("metric")["value"]
    print(f"Analyzed {summary['total_postings']} postings")
    print(f"Found {summary['unique_skills']} unique skills")
    print(
        f"Classified {summary['beginner_friendly_postings']} as beginner-friendly "
        f"and {summary['advanced_postings']} as advanced"
    )
    print(f"Wrote {len(outputs)} analysis files to {args.output_dir}")


if __name__ == "__main__":
    main()
