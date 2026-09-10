# Phase 1 — Personal Skill-Gap Analyzer

## Goal

Let users select skills, compare them with each posting's detected skills, and
receive an explainable overlap score and learning priorities. The score must be
called **skill overlap**, never a hiring prediction. Matching rules are documented
in [`../skill-gap-analyzer.md`](../skill-gap-analyzer.md).

## Milestones

### ✅ Milestone 1 — Define matching rules

#### What was implemented

This milestone produced the written specification in
[`../skill-gap-analyzer.md`](../skill-gap-analyzer.md). It defines the calculation
as matched detected skills divided by the posting's total detected skills, along
with case normalization, duplicate removal, canonical naming, rounding, and
empty-data behavior. It also defines the future function's result fields:
`matched_skills`, `missing_skills`, `matched_count`, `required_count`, and
`match_percentage`.

No runtime calculation code was added in this milestone. Its purpose was to make
the upcoming implementation testable and prevent the result from being presented
as a hiring prediction. The specification requires the UI to call it **skill
overlap** and document what the score does not measure.

### ✅ Milestone 2 — Build the skill-selection interface — Day 1

- Add a searchable multiselect containing canonical catalog skills.
- Store selections in Streamlit session state.
- Display the selected-skill count and a clear-selection button.
- Show a useful empty state before skills are selected.

Done when users can select, retain, and clear skills without changing source CSVs.

#### What was implemented

The `My Skills` section was added to [`../../app.py`](../../app.py). It imports
`SKILL_CATALOG` from `src/extract_skills.py` and flattens that catalog into one
alphabetically sorted list, ensuring profile choices use the same canonical names
as the extraction pipeline.

Streamlit's `st.multiselect` provides searchable selection and stores the result
under the `profile_skills` session-state key, so selections remain available when
the app reruns. The surrounding section:

- Shows a singular or plural count as skills are selected.
- Shows instructions when the profile is empty.
- Disables `Clear my skills` when there is nothing to clear.
- Clears the session-state list through the button callback.
- Calculates everything in memory and never writes to the source CSV files.

An automated Streamlit smoke test exercised catalog loading, selecting `Python`
and `SQL`, persistence after rerun, count display, the clear action, and the empty
state. The matching percentage is intentionally deferred to Milestone 3.

### ✅ Milestone 3 — Implement and test matching logic — Day 2

- Create `src/skill_gap.py` with a pure matching function.
- Normalize case, whitespace, duplicates, nulls, and empty values.
- Return matched skills, missing skills, counts, and percentage.
- Return `None` when a posting has no detected catalog skills.
- Add unit tests for all documented edge cases.

Done when matching works independently of Streamlit and all tests pass.

#### What was implemented

[`../../src/skill_gap.py`](../../src/skill_gap.py) now contains a pure
`calculate_skill_gap` function and a typed result contract. Its normalization
helper trims whitespace, compares case-insensitively, removes duplicates, ignores
null/blank/unknown skills, restores canonical catalog spelling, and sorts results
deterministically. A plain string is rejected to prevent accidental character-by-
character matching of serialized CSV data.

The calculation returns matched and missing skills, both counts, and a percentage
rounded to one decimal. When a posting has no detected catalog skills it returns
`None`, preserving the documented distinction between unavailable data and 0%.

[`../../tests/test_skill_gap.py`](../../tests/test_skill_gap.py) covers partial,
full, zero, and unavailable overlap; empty inputs; capitalization; whitespace;
duplicates; nulls; unknown skills; invalid string input; and input immutability.

### ✅ Milestone 4 — Score visible postings — Day 3

- Apply matching to the currently filtered dataframe.
- Keep results in memory rather than changing processed CSVs.
- Verify existing company, title, skill, and difficulty filters.
- Test multiple postings and empty user selections.

Done when every visible posting has a correct result or an explained unavailable state.

#### What was implemented

`score_postings` in [`../../src/skill_gap.py`](../../src/skill_gap.py) accepts a
dataframe and the selected profile skills. It splits each pipe-delimited
`skills_extracted` value, calls the tested single-posting matcher, and attaches
five result columns to a deep copy. The source dataframe and CSV files remain
unchanged. It validates the required input column and preserves `None` for jobs
without detected skills. Tests cover multiple rows, unavailable results, missing
columns, and input immutability.

### ✅ Milestone 5 — Add results to the dashboard — Day 4

- Add skill-overlap percentage to the opportunity table.
- Show matched and missing skills in selected-job details.
- Add average-overlap and strongest-match metrics.
- Explain unavailable scores without treating them as zero.
- Check desktop and narrow layouts.

Done when users can understand both the score and its evidence.

#### What was implemented

[`../../app.py`](../../app.py) scores the dataframe after normal dashboard filters
run. When a profile exists, the My Skills section shows average overlap, strongest
overlap, and the number visible at the selected threshold. The opportunity table
adds a `Skill overlap` percentage. Selecting a row shows its matched skills,
missing skills, and an explicit notice that the number is catalog overlap—not a
qualification or interview prediction. Unavailable scores remain distinct from 0%.

### ✅ Milestone 6 — Prioritize opportunities and skills — Day 5

- Sort postings by highest overlap and add a minimum-overlap filter.
- Rank missing skills by the number of relevant postings requesting them.
- Add a concise “Learn next” section.
- Run unit tests, app smoke tests, and manual UI checks.
- Update the README, architecture guide, and Current trackers.

Done when the full skill-gap workflow is interview-demo ready.

#### What was implemented

The My Skills panel now includes a minimum-overlap slider. Matching postings are
sorted from highest overlap to lowest while jobs without enough detected data are
kept and shown last. `rank_missing_skills` in `src/skill_gap.py` explodes the
in-memory missing-skill lists, counts the number of visible postings requesting
each skill, and returns a deterministic ranking for the `Learn next` table.

The feature was validated with 14 focused skill-gap tests, the full 27-test project
suite, and a Streamlit smoke test that selected profile skills and changed the
minimum threshold. Phase 1 is complete; no later roadmap phase was implemented.

## Phase demonstration

Select `Python` and `SQL`, filter to a company, show ranked opportunities, open
one result, explain its score, and show the missing skills recommended next.
