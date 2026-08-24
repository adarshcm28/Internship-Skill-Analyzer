"""Create static charts from the Step 5 skill-analysis outputs."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "isa-matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_ANALYSIS_DIR = Path("data/processed/analysis")
DEFAULT_OUTPUT_DIR = Path("reports/figures")

NAVY = "#172033"
PURPLE = "#5B5CE2"
TEAL = "#18A47B"
ORANGE = "#ED9F2D"
LIGHT_PURPLE = "#9B9CF2"
GRID = "#DDE2EC"


def set_chart_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": GRID,
            "axes.labelcolor": NAVY,
            "axes.titlecolor": NAVY,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "font.family": "sans-serif",
            "font.size": 10,
            "text.color": NAVY,
            "xtick.color": NAVY,
            "ytick.color": NAVY,
            "grid.color": GRID,
            "grid.alpha": 0.7,
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_top_skills(skill_summary: pd.DataFrame, output_path: Path) -> None:
    top = skill_summary.head(10).sort_values("posting_count")
    fig, ax = plt.subplots(figsize=(9, 5.8))
    bars = ax.barh(top["skill"], top["percentage"], color=PURPLE, height=0.64)
    ax.set_title("Top 10 Most Requested Skills", loc="left", pad=14)
    ax.set_xlabel("Percentage of internship postings")
    ax.set_ylabel("Skill")
    ax.set_xlim(0, max(100, float(top["percentage"].max()) + 12))
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.bar_label(bars, labels=[f"{value:.1f}%" for value in top["percentage"]], padding=5)
    fig.tight_layout()
    save_figure(fig, output_path)


def plot_categories(category_summary: pd.DataFrame, output_path: Path) -> None:
    categories = category_summary.sort_values("posting_count")
    colors = [LIGHT_PURPLE if category != "Programming Languages" else PURPLE for category in categories["category"]]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.barh(categories["category"], categories["percentage_of_postings"], color=colors, height=0.62)
    ax.set_title("Skill Categories Mentioned in Postings", loc="left", pad=14)
    ax.set_xlabel("Percentage of internship postings")
    ax.set_ylabel("Category")
    ax.set_xlim(0, 110)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.bar_label(
        bars,
        labels=[f"{value:.1f}%" for value in categories["percentage_of_postings"]],
        padding=5,
    )
    fig.tight_layout()
    save_figure(fig, output_path)


def plot_skill_heatmap(
    posting_skills: pd.DataFrame,
    skill_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    top_skills = skill_summary.head(10)["skill"].tolist()
    filtered = posting_skills[posting_skills["skill"].isin(top_skills)]
    matrix = pd.crosstab(filtered["skill"], filtered["posting_id"])
    co_occurrence = matrix.dot(matrix.T).reindex(
        index=top_skills, columns=top_skills, fill_value=0
    )
    for skill in top_skills:
        co_occurrence.loc[skill, skill] = 0

    fig, ax = plt.subplots(figsize=(8.7, 7.3))
    image = ax.imshow(co_occurrence, cmap="Purples", vmin=0, aspect="equal")
    ax.set_title("Top-Skill Co-occurrence", loc="left", pad=14)
    ax.set_xlabel("Skill")
    ax.set_ylabel("Skill")
    ax.set_xticks(range(len(top_skills)), labels=top_skills, rotation=45, ha="right")
    ax.set_yticks(range(len(top_skills)), labels=top_skills)

    threshold = float(co_occurrence.values.max()) / 2
    for row in range(len(top_skills)):
        for column in range(len(top_skills)):
            value = int(co_occurrence.iloc[row, column])
            if row != column and value:
                ax.text(
                    column,
                    row,
                    str(value),
                    ha="center",
                    va="center",
                    color="white" if value > threshold else NAVY,
                    fontsize=9,
                )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("Postings mentioning both skills")
    fig.tight_layout()
    save_figure(fig, output_path)


def plot_experience_levels(posting_difficulty: pd.DataFrame, output_path: Path) -> None:
    order = ["Beginner-friendly", "Advanced"]
    counts = posting_difficulty["experience_level"].value_counts().reindex(order, fill_value=0)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    bars = ax.bar(counts.index, counts.values, color=[TEAL, ORANGE], width=0.56)
    ax.set_title("Beginner-Friendly vs. Advanced Postings", loc="left", pad=14)
    ax.set_xlabel("Experience classification")
    ax.set_ylabel("Number of internship postings")
    ax.set_ylim(0, max(counts.max() + 2, 5))
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.bar_label(bars, labels=[str(value) for value in counts.values], padding=5, fontsize=12)
    fig.text(
        0.5,
        0.01,
        "Advanced = at least two skills from the documented advanced-skill set",
        ha="center",
        color="#667085",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save_figure(fig, output_path)


def create_visualizations(analysis_dir: Path, output_dir: Path) -> list[Path]:
    required_files = [
        "skill_summary.csv",
        "category_summary.csv",
        "posting_difficulty.csv",
    ]
    missing = [name for name in required_files if not (analysis_dir / name).exists()]
    posting_skills_path = analysis_dir.parent / "posting_skills.csv"
    if not posting_skills_path.exists():
        missing.append(str(posting_skills_path))
    if missing:
        raise FileNotFoundError(f"Missing analysis input(s): {', '.join(missing)}")

    skill_summary = pd.read_csv(analysis_dir / "skill_summary.csv")
    category_summary = pd.read_csv(analysis_dir / "category_summary.csv")
    posting_difficulty = pd.read_csv(analysis_dir / "posting_difficulty.csv")
    posting_skills = pd.read_csv(posting_skills_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        output_dir / "top-10-skills.png",
        output_dir / "skill-categories.png",
        output_dir / "skill-combinations-heatmap.png",
        output_dir / "posting-difficulty.png",
    ]
    plot_top_skills(skill_summary, outputs[0])
    plot_categories(category_summary, outputs[1])
    plot_skill_heatmap(posting_skills, skill_summary, outputs[2])
    plot_experience_levels(posting_difficulty, outputs[3])
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create internship-skill charts.")
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = create_visualizations(args.analysis_dir, args.output_dir)
    print(f"Created {len(outputs)} charts:")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    main()
