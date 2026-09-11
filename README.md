# AI-Powered Data Science Internship Skill Tracker

## Project Overview

The **AI-Powered Data Science Internship Skill Tracker** is a beginner-friendly data science project that analyzes data science internship and entry-level job postings to answer one practical question:

> What skills do companies actually ask for, and what should I learn next?

Instead of working with a generic practice dataset, this project uses job posting text to discover real skill trends for data science students. The final version of the project will let a user explore common internship requirements, view charts of in-demand skills, and paste in a job description to receive an AI-generated skill breakdown and learning plan.

This project is designed for a beginner data science student who wants to practice Python, data cleaning, visualization, basic natural language processing, and AI-assisted analysis while building something useful for their own career.

## Architecture and Interview Documentation

See the [project architecture guide](docs/project-architecture.md) for the
end-to-end system map, provider architecture, data lineage, analysis logic,
generated charts, engineering tradeoffs, and an interview-ready walkthrough.

The [personal skill-gap analyzer specification](docs/skill-gap-analyzer.md)
documents the matching formula, edge cases, result contract, interpretation,
and limitations for that planned feature.

## Current

- **Completed foundation:** Phase 1 — Personal Skill-Gap Analyzer
- **Current phase:** Phase 4 — Internship Agent Tools
- **Completed:** Phase 3 — Personalized AI Career Coach; Phase 4 Milestone 1 — Internship search tool
- **Current milestone:** Phase 4, Milestone 2 — Internship comparison tool
- **Roadmap day:** Day 9 of 14
- **AI roadmap:** [Open the Internship Assistant roadmap](docs/roadmap/README.md)

The roadmap contains fourteen daily milestones centered on improving the existing
Internship Assistant. Update this section and the roadmap after completing each
milestone.

## Problem Statement

Data science students often ask:

- Which skills should I learn first?
- Are Python and SQL enough for internships?
- How often do companies ask for machine learning?
- Do I need Tableau, Excel, cloud tools, or deep learning?
- How can I compare my current skills to a real internship posting?

This project helps answer those questions by collecting internship descriptions, extracting skills from the text, and turning the results into simple insights.

## Main Features

The completed app should include:

- A dataset of 50-200 data science internship or entry-level job postings
- Text cleaning for messy job descriptions
- Skill extraction for tools, programming languages, statistics, machine learning, and soft skills
- Charts showing the most common skills and tools
- Analysis of beginner-friendly versus advanced requirements
- A Streamlit dashboard for exploring results
- An AI-powered job description analyzer
- A personalized learning recommendation feature

## Example Questions This Project Can Answer

- What are the top 10 skills requested in data science internships?
- How often do postings mention Python, SQL, Excel, Tableau, or machine learning?
- Which skills commonly appear together?
- Which job postings seem beginner-friendly?
- What skills am I missing for a specific internship?
- What should I learn next based on a job description?

## Tech Stack

| Tool | Purpose |
| --- | --- |
| Python | Main programming language |
| Pandas | Data cleaning and analysis |
| Matplotlib or Plotly | Data visualization |
| Streamlit | Interactive dashboard |
| OpenAI API or another AI model | Skill extraction and recommendations |
| Jupyter Notebook | Optional exploration and experimentation |
| GitHub | Version control and portfolio sharing |

## Suggested Project Structure

```text
Internship-Skill-Analyzer/
├── data/
│   ├── raw/
│   │   └── internship_postings.csv
│   └── processed/
│       └── cleaned_postings.csv
├── notebooks/
│   └── exploration.ipynb
├── src/
│   ├── clean_text.py
│   ├── extract_skills.py
│   ├── analyze_skills.py
│   └── ai_recommender.py
├── app.py
├── requirements.txt
├── .env.example
└── README.md
```

This structure can be built gradually. You do not need every file on day one.

## Dataset Plan

Start with a small dataset of internship descriptions. A beginner-friendly goal is 50 postings. A stronger portfolio version can use 100-200 postings.

Each row in the dataset should include:

| Column | Description |
| --- | --- |
| `job_title` | Name of the role |
| `company` | Company name |
| `location` | Job location or remote status |
| `description` | Full job description text |
| `source` | Where the posting came from |
| `date_collected` | Date the posting was collected |

Example:

```csv
job_title,company,location,description,source,date_collected
Data Science Intern,Example Company,Remote,"We are looking for a student with Python, SQL, Excel, and statistics experience.",Manual,2026-08-18
```

## Important Note About Data Collection

When collecting job postings, use public datasets or manually collect a small number of descriptions for learning purposes. Do not scrape websites that prohibit scraping in their terms of service. If you copy descriptions manually, keep the dataset small and use it only for educational analysis.

## Step-By-Step Build Plan

### Step 1: Set Up the Project

Create the basic project files and folders:

```bash
mkdir -p data/raw data/processed notebooks src
touch app.py requirements.txt .env.example
```

Add the main Python libraries to `requirements.txt`:

```text
pandas
numpy
matplotlib
plotly
streamlit
python-dotenv
openai
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Collect Job Posting Data

The collector now retains only postings with confirmed US location evidence.
Unspecified remote and worldwide roles are excluded; see the collection guide
for multi-location handling and limitations.

Company job boards are configured in:

```text
config/job_boards.json
```

The collector checks 32 configured company boards through structured Ashby,
Lever, Greenhouse, Amazon Jobs, and Workday career feeds for US data and
software internships. Amazon and Intel are now included as large-company
career-system connectors. Results are capped at five postings per company.
The August 29, 2026 refresh retained 23 postings from 13 companies, including
five Amazon postings and one Intel posting.
Updated US charts are in `reports/figures/us/`; the earlier worldwide charts
remain separate. Test the live collection without changing the current
dataset:

```bash
python -m src.collect_postings --dry-run
```

After a successful dry run, create the raw dataset:

```bash
python -m src.collect_postings
```

The generated `data/raw/us_internship_postings.csv` records the title, company,
location, full public description, source URL, collection date, provider,
external posting ID, publication time, employment type, and workplace type.
To keep the analysis balanced, the collector retains at most five postings per
company by default; use `--max-per-company` to change that limit.
See `docs/data-collection.md` for API details, filtering rules, validation, and
configuration instructions.

### Open the dashboard

Launch the interactive user interface from the project folder:

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in a browser. The dashboard reads the latest
US processed data and provides company, skill, difficulty, and title filters,
interactive charts, an opportunity table, and links to the original postings.

Select skills under **My Skills** to create a 2-, 4-, 8-, or 12-week structured
learning plan. Select an internship row and choose **Ask Internship Assistant**
for posting-specific preparation help. You can also ask the assistant to find
visible internships by company, title, US location, skills, difficulty, or
minimum skill overlap; searches remain limited to the current dashboard data.

### Internship Assistant setup

The dashboard includes an **Internship Assistant** chat panel. To enable replies,
add `OPENAI_API_KEY` to the local `.env` file (already excluded from Git):

```dotenv
OPENAI_API_KEY=your_actual_key
OPENAI_MODEL=gpt-5.6-luna
```

Refresh the dashboard after saving. Do not share or commit the actual key.
The model is configurable with `OPENAI_MODEL`; access and API billing are required.
Open the assistant panel and select **Check connection**. Detecting a key only
confirms that configuration exists; the check validates authentication and access
to the configured model without generating a chat response. See the
[Internship Assistant guide](docs/internship-assistant.md) for status meanings
and security details.
Chat sends the question, recent conversation, and filtered job data to OpenAI only
when submitted. Descriptions are excerpted, chat history is bounded, and changing
filters resets the conversation. The bot does not browse or submit applications.
Without a key, the panel remains visible but AI replies are disabled.
The API logic lives in `src/chatbot.py` and uses the
[Responses API](https://developers.openai.com/api/docs/quickstart).

### Step 3: Clean the Text

Job descriptions are messy. They may include bullet points, repeated spaces, inconsistent capitalization, and extra symbols.

Cleaning should include:

- Convert text to lowercase
- Remove extra spaces
- Remove unnecessary punctuation
- Handle missing descriptions
- Standardize common terms

Example cleaning goals:

- `Machine Learning` becomes `machine learning`
- `SQL, Python, and Excel required!` becomes easier to search
- Empty descriptions are removed or flagged

### Step 4: Extract Skills

Start with a simple keyword-based skill extractor before adding AI.

Example skill categories:

**Programming Languages**

- Python
- R
- SQL

**Data Tools**

- Excel
- Tableau
- Power BI
- Jupyter

**Machine Learning**

- Machine learning
- Deep learning
- NLP
- Computer vision

**Statistics and Math**

- Statistics
- Probability
- A/B testing
- Regression

**Soft Skills**

- Communication
- Collaboration
- Problem solving
- Presentation

The first version can count whether each skill appears in a job description.

### Step 5: Analyze Skill Trends

Use Pandas to calculate:

- Total number of postings analyzed
- Most common skills
- Percentage of postings mentioning each skill
- Most common skill categories
- Skill combinations, such as Python + SQL
- Beginner-friendly postings versus advanced postings

Example outputs:

| Skill | Count | Percentage |
| --- | ---: | ---: |
| Python | 42 | 84% |
| SQL | 37 | 74% |
| Excel | 29 | 58% |
| Tableau | 18 | 36% |

### Step 6: Create Visualizations

Create charts such as:

- Bar chart of top skills
- Pie chart or bar chart of skill categories
- Heatmap of skill combinations
- Beginner versus advanced posting comparison

Recommended beginner chart:

```text
Top 10 Most Requested Skills
```

This is simple, readable, and immediately useful.

### Step 7: Build the Streamlit Dashboard

The dashboard should allow users to:

- View the total number of postings analyzed
- See the most common skills
- Filter by company, location, or job title
- Explore charts
- Paste in a new job description
- Get extracted skills and recommendations

Possible dashboard sections:

- Overview
- Skill Trends
- Job Posting Explorer
- AI Job Description Analyzer
- Learning Plan

Run the app with:

```bash
streamlit run app.py
```

### Step 8: Add the AI Feature

The AI feature should let a user paste a job description and receive:

- Required technical skills
- Required soft skills
- Nice-to-have skills
- Beginner-friendly explanation
- Suggested learning plan

Example prompt idea:

```text
You are helping a beginner data science student understand an internship posting.
Extract the required skills, separate technical skills from soft skills, and suggest a simple learning plan.
Return the answer in clear bullet points.
```

Store API keys in a `.env` file, not directly in code.

`.env.example`:

```text
OPENAI_API_KEY=your_api_key_here
```

### Step 9: Compare User Skills to a Job Posting

Add a text input where the user enters skills they already know:

```text
Python, Excel, basic statistics
```

Then compare those skills to the extracted job requirements.

The app should show:

- Skills already matched
- Missing skills
- Recommended next skills to learn
- A short learning plan

### Step 10: Polish the Project for a Portfolio

Before sharing the project, add:

- Screenshots of the dashboard
- A short project summary
- Clear setup instructions
- A sample dataset or sample data format
- A list of limitations
- Future improvements

## Beginner-Friendly Development Milestones

### Milestone 1: Basic Data Analysis

Goal:

- Load the CSV file
- Clean job descriptions
- Count skill keywords
- Print the top skills

What this teaches:

- Pandas basics
- String cleaning
- Simple feature extraction

### Milestone 2: Visualizations

Goal:

- Create charts for top skills
- Save or display charts

What this teaches:

- Data visualization
- Communicating insights
- Ranking and grouping data

### Milestone 3: Streamlit App

Goal:

- Build a simple dashboard
- Display charts interactively

What this teaches:

- Turning analysis into a usable app
- User interface basics
- Sharing data science work

### Milestone 4: AI Skill Extraction

Goal:

- Paste a job description
- Use AI to identify required skills
- Summarize the posting

What this teaches:

- Prompt design
- AI-assisted analysis
- Responsible use of language models

### Milestone 5: Personalized Learning Plan

Goal:

- Compare job requirements to user skills
- Recommend what to learn next

What this teaches:

- Basic recommendation logic
- Practical career-focused analysis
- Building a more useful final product

## Example User Flow

1. User opens the Streamlit app.
2. User sees the most common skills across internship postings.
3. User filters postings by role or location.
4. User pastes a new internship description.
5. The app extracts required skills.
6. User enters their current skills.
7. The app shows missing skills and a suggested learning plan.

## Possible AI Output

If a user pastes a job description, the app might return:

```text
Required technical skills:
- Python
- SQL
- Statistics
- Data visualization

Soft skills:
- Communication
- Teamwork
- Problem solving

You already match:
- Python
- Statistics

You may want to learn next:
- SQL
- Tableau or Power BI

Suggested 3-week learning plan:
Week 1: Practice SQL SELECT, WHERE, JOIN, and GROUP BY.
Week 2: Build a small dashboard using Tableau, Power BI, or Plotly.
Week 3: Complete a mini project combining Python, SQL, and visualization.
```

## Responsible AI Use

AI output should be treated as helpful guidance, not absolute truth. Job descriptions can be vague, and AI models may miss skills or infer skills that are not explicitly listed.

Good practices:

- Show the original job description alongside AI output
- Let users review extracted skills
- Use clear labels like "AI-generated recommendation"
- Avoid making promises about employability
- Keep API keys private

## Limitations

This project has some natural limitations:

- A small dataset may not represent the entire job market
- Manually collected postings can introduce bias
- Keyword matching may miss skills written in unusual ways
- AI extraction may produce imperfect results
- Skill demand changes over time

These limitations are normal for a beginner project and can be discussed honestly in a portfolio or presentation.

## Future Improvements

Possible upgrades:

- Add more job postings over time
- Compare internship postings by city, remote status, or company type
- Add resume skill matching
- Use embeddings to find similar job postings
- Track skill trends month by month
- Add downloadable reports
- Deploy the Streamlit app online
- Add a database for storing postings
- Improve AI prompts and validation

## Why This Project Is Valuable

This project shows more than basic chart-making. It demonstrates that you can:

- Ask a useful real-world question
- Work with messy text data
- Clean and structure data
- Extract patterns from unstructured information
- Visualize insights clearly
- Use AI responsibly
- Build a small interactive app
- Explain technical findings to a non-technical audience

That makes it a strong portfolio project for a beginner data science student.

## Final Project Goal

By the end of this project, you should have a working dashboard that helps data science students understand internship skill requirements and decide what to learn next.

Final title:

```text
AI-Powered Data Science Internship Skill Tracker
```

## UI preview

Open [`sample-ui.html`](sample-ui.html) in a web browser to view the responsive dashboard concept.
