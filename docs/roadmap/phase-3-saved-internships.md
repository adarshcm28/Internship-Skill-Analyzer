# Phase 3 — Saved Internships

## Goal

Let users bookmark opportunities and return to a focused list without changing
the collected dataset.

## Milestones

### ⬜ Milestone 1 — Add bookmark interactions — Day 10

- Store saved posting IDs in Streamlit session state.
- Add Save and Remove actions with clear feedback.
- Create a saved-internships view with details and source links.
- Handle duplicate saves and postings no longer in the dataset.
- Test bookmark state operations.

Done when saving and removing works for the active browser session.

### ⬜ Milestone 2 — Add safe local persistence — Day 11

- Store only posting IDs and preferences in a Git-ignored local profile.
- Validate the profile before loading and recover from invalid data.
- Add a clear-saved-data action with confirmation.
- Document privacy, single-user limitations, and a future database path.
- Run tests and update Current trackers.

Done when bookmarks survive an app restart without entering Git history.
