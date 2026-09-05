# Personal Skill-Gap Analyzer — Matching Specification

**Status:** Milestone 1 complete — rules defined; calculation code and UI are not yet implemented.

## Purpose

The personal skill-gap analyzer will compare skills selected by a user with the
skills detected in each internship posting. It will explain which skills overlap,
which detected skills are missing from the user's profile, and the percentage of
detected job skills the user selected.

This is a transparent keyword-overlap tool. It is not an employability score,
application recommendation, or prediction of whether a candidate will receive an
interview.

## Inputs

The matching function will accept two collections:

1. `job_skills`: canonical skills detected in one posting by
   `src/extract_skills.py`.
2. `user_skills`: canonical skills selected by the user from the same catalog.

Examples of canonical skills include `Python`, `SQL`, `Tableau`, and
`Machine Learning`.

## Normalization rules

Before comparison, both collections will be normalized as follows:

1. Remove empty and null values.
2. Trim leading and trailing whitespace.
3. Compare names case-insensitively.
4. Remove duplicates.
5. Return skill names using the canonical spelling from the project skill catalog.
6. Sort returned skill lists consistently so results are deterministic.

Skills outside the project catalog will not affect the first version of the score.
The UI will let users select catalog skills, which avoids ambiguous free-text input.

## Matching rules

For one posting:

```text
matched skills = job skills ∩ user skills
missing skills = job skills − user skills
matched count = number of matched skills
required count = number of unique detected job skills
match percentage = (matched count ÷ required count) × 100
```

The percentage will be rounded to the nearest whole number for display. Internal
calculations may retain greater precision.

### Example

```text
Detected job skills: Python, SQL, Tableau
Selected user skills: Python, SQL, Git

Matched skills: Python, SQL
Missing skills: Tableau
Matched count: 2
Required count: 3
Match percentage: 67%
```

`Git` does not increase or decrease this posting's score because it was not
detected in that posting.

## Empty-value behavior

| Situation | Result |
| --- | --- |
| Posting has skills; user selected none | `0%`, with every job skill listed as missing |
| User has all detected job skills | `100%`, with no missing skills |
| Posting has no detected skills | Percentage is unavailable, not `0%` or `100%` |
| Both collections are empty | Percentage is unavailable |
| Either collection contains duplicates | Duplicates are ignored |
| Capitalization differs | Skills still match |

An unavailable percentage will be represented internally as `None` and displayed
as `Not enough detected skill data`. Treating it as zero would incorrectly imply
that the user lacks skills when the extractor simply found no catalog skills.

## Output contract

The future matching function will return one result with this structure:

```python
{
    "matched_skills": ["Python", "SQL"],
    "missing_skills": ["Tableau"],
    "matched_count": 2,
    "required_count": 3,
    "match_percentage": 66.7,
}
```

For a posting with no detected skills:

```python
{
    "matched_skills": [],
    "missing_skills": [],
    "matched_count": 0,
    "required_count": 0,
    "match_percentage": None,
}
```

## Interpretation in the interface

The UI will call the result **Skill overlap**, not job fit or qualification score.
It will always show the reason behind the number:

```text
Skill overlap: 67%
You selected: Python, SQL
Not selected: Tableau
```

The first version will not attach labels such as `qualified`, `unqualified`,
`good candidate`, or `likely interview`. Any optional display bands added later
must be labeled as navigation aids rather than hiring predictions.

## Scope and limitations

- The score only considers skills detectable by the catalog in
  `src/extract_skills.py`.
- It does not measure proficiency, years of experience, education, portfolio
  quality, work authorization, location preference, or cultural fit.
- A skill appearing in a description is not necessarily a strict requirement.
- The extractor can miss synonyms and skills that are not in its catalog.
- User-selected skills are self-reported and are not verified.
- Every unique skill has equal weight in Milestone 1.
- Soft skills and technical skills count equally in the initial formula.
- A high percentage does not mean the posting is current; users must check the
  original application link.
- Results depend on the current collected dataset and change when it is refreshed.

## Acceptance criteria for Milestone 1

Milestone 1 is complete when this specification documents:

- The two inputs and their source.
- Normalization and duplicate-handling rules.
- The exact match formula.
- Expected output fields.
- Empty-data behavior.
- User-facing terminology.
- Limitations that prevent the score from being presented as an employment
  prediction.

The next milestone is the Streamlit skill-selection interface. Matching logic will
be implemented separately in Milestone 3 so UI state and calculation logic remain
independently testable.
