# Phase 2 — Side-by-Side Job Comparison

## Goal

Allow users to select two or three internships and compare skills, difficulty,
location, company, and application links on one screen.

## Milestones

### ⬜ Milestone 1 — Define comparison behavior — Day 6

- Decide which fields appear and how postings are added or removed.
- Limit comparison to three unique postings.
- Define empty, one-job, duplicate, and maximum-selection states.
- Store selected posting IDs in session state.

Done when behavior is documented and selection state works.

### ⬜ Milestone 2 — Build the comparison model — Day 7

- Create a pure function accepting selected IDs and posting data.
- Calculate shared skills and skills unique to each posting.
- Preserve a stable posting order.
- Test missing IDs, duplicates, and empty skill lists.

Done when a tested result can be produced without Streamlit.

### ⬜ Milestone 3 — Create the comparison interface — Day 8

- Add Compare actions to the opportunities area.
- Display two or three responsive comparison columns.
- Show shared and unique skills using labels, not color alone.
- Include difficulty explanations and application links.

Done when the comparison is clear at desktop and narrow widths.

### ⬜ Milestone 4 — Refine and validate — Day 9

- Add clear-all and individual remove controls.
- Add helpful empty and maximum-selection states.
- Run unit tests, app smoke tests, and manual interaction checks.
- Update documentation and Current trackers.

Done when the feature can be demonstrated without confusing selection behavior.
