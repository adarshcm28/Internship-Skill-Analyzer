# Phase 1 — Personal Skill-Gap Analyzer

## Goal

Let users select skills, compare them with each posting's detected skills, and
receive an explainable overlap score and learning priorities. The score must be
called **skill overlap**, never a hiring prediction. Matching rules are documented
in [`../skill-gap-analyzer.md`](../skill-gap-analyzer.md).

## Milestones

### ✅ Milestone 1 — Define matching rules

Completed: formula, normalization, empty-data behavior, output contract, UI
terminology, and limitations.

### 🚧 Milestone 2 — Build the skill-selection interface — Day 1

- Add a searchable multiselect containing canonical catalog skills.
- Store selections in Streamlit session state.
- Display the selected-skill count and a clear-selection button.
- Show a useful empty state before skills are selected.

Done when users can select, retain, and clear skills without changing source CSVs.

### ⬜ Milestone 3 — Implement and test matching logic — Day 2

- Create `src/skill_gap.py` with a pure matching function.
- Normalize case, whitespace, duplicates, nulls, and empty values.
- Return matched skills, missing skills, counts, and percentage.
- Return `None` when a posting has no detected catalog skills.
- Add unit tests for all documented edge cases.

Done when matching works independently of Streamlit and all tests pass.

### ⬜ Milestone 4 — Score visible postings — Day 3

- Apply matching to the currently filtered dataframe.
- Keep results in memory rather than changing processed CSVs.
- Verify existing company, title, skill, and difficulty filters.
- Test multiple postings and empty user selections.

Done when every visible posting has a correct result or an explained unavailable state.

### ⬜ Milestone 5 — Add results to the dashboard — Day 4

- Add skill-overlap percentage to the opportunity table.
- Show matched and missing skills in selected-job details.
- Add average-overlap and strongest-match metrics.
- Explain unavailable scores without treating them as zero.
- Check desktop and narrow layouts.

Done when users can understand both the score and its evidence.

### ⬜ Milestone 6 — Prioritize opportunities and skills — Day 5

- Sort postings by highest overlap and add a minimum-overlap filter.
- Rank missing skills by the number of relevant postings requesting them.
- Add a concise “Learn next” section.
- Run unit tests, app smoke tests, and manual UI checks.
- Update the README, architecture guide, and Current trackers.

Done when the full skill-gap workflow is interview-demo ready.

## Phase demonstration

Select `Python` and `SQL`, filter to a company, show ranked opportunities, open
one result, explain its score, and show the missing skills recommended next.
