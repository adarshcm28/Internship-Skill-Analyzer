# Internship Skill Analyzer Interview Demo

## Setup

From the repository root, install dependencies and run the application:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Add a local `.env` only when demonstrating AI features. Never show the key on
screen. Use a synthetic resume for the upload portion.

## Seven minute walkthrough

### 1. Problem and data

Explain that the project collects US internship postings from structured public
career feeds, normalizes descriptions, extracts a documented skill catalog, and
keeps source URLs for traceability.

### 2. Market exploration

Use company, location, title, skill, and difficulty filters. Point out that the
charts and counts recompute over the visible rows.

### 3. Deterministic personalization

Select Python and SQL under **My Skills**. Show match percentages, missing skills,
and learning priorities. Explain that pandas and project code calculate these
values; the language model does not invent them.

### 4. Candidate Profile

Upload a synthetic TXT or DOCX resume. Correct one extracted field, review the
detected skills, and show the ranked internship matches. Emphasize local parsing,
session-only state, consent, and the delete action.

### 5. Grounded assistant and tools

Ask: “Find beginner-friendly Python internships and summarize the most requested
skills.” Expand **How this answer was produced** to show the search and market
tools. Open a cited company source.

### 6. Handled failure

Ask the assistant to submit an application or provide a posting ID outside the
current selection. Show that it refuses the unsupported action or returns a safe
tool error instead of inventing a result.

### 7. Engineering evidence

Open **Developer diagnostics** to show latency, tool-call count, citation count,
and token usage. Mention the offline evaluation cases and automated tests.

## Interview summary

“I built an end-to-end internship intelligence application: multi-provider data
collection, deterministic NLP and matching, interactive analysis, privacy-aware
resume parsing, and a grounded tool-using assistant. I separated calculations
from generation, preserved source traceability, tested failure cases without paid
API calls, and documented the remaining production risks.”
