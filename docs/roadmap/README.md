# Two-Week Feature Roadmap

This folder breaks additional features into daily, demonstrable milestones. Each
day ends with a deliverable that can be tested, documented, and committed.

## Current

| Item | Status |
| --- | --- |
| Current phase | Phase 1 — Personal Skill-Gap Analyzer |
| Last completed milestone | Milestone 1 — Matching specification |
| Current milestone | Milestone 2 — Skill-selection interface |
| Next daily task | Day 1 |

Status: ✅ Complete · 🚧 Current · ⬜ Not started

## Phases

| Phase | Feature | Milestones | Days |
| --- | --- | ---: | ---: |
| [Phase 1](phase-1-skill-gap.md) | Personal Skill-Gap Analyzer | 2–6 | 1–5 |
| [Phase 2](phase-2-job-comparison.md) | Side-by-Side Job Comparison | 1–4 | 6–9 |
| [Phase 3](phase-3-saved-internships.md) | Saved Internships | 1–2 | 10–11 |
| [Phase 4](phase-4-data-quality.md) | Data Quality and Posting Freshness | 1–3 | 12–14 |

## Fourteen-day schedule

| Day | Phase and milestone | Deliverable | Status |
| ---: | --- | --- | :---: |
| 1 | Phase 1, Milestone 2 | Searchable current-skills selector | 🚧 |
| 2 | Phase 1, Milestone 3 | Tested matching function | ⬜ |
| 3 | Phase 1, Milestone 4 | Scores for every visible posting | ⬜ |
| 4 | Phase 1, Milestone 5 | Match explanations in the UI | ⬜ |
| 5 | Phase 1, Milestone 6 | Sorting, recommendations, and final tests | ⬜ |
| 6 | Phase 2, Milestone 1 | Comparison rules and selection state | ⬜ |
| 7 | Phase 2, Milestone 2 | Tested comparison data model | ⬜ |
| 8 | Phase 2, Milestone 3 | Side-by-side comparison UI | ⬜ |
| 9 | Phase 2, Milestone 4 | Comparison UX and tests | ⬜ |
| 10 | Phase 3, Milestone 1 | Save/remove controls and saved-jobs view | ⬜ |
| 11 | Phase 3, Milestone 2 | Local persistence and privacy notes | ⬜ |
| 12 | Phase 4, Milestone 1 | Collection diagnostics and exclusion counters | ⬜ |
| 13 | Phase 4, Milestone 2 | First-seen, last-seen, and status tracking | ⬜ |
| 14 | Phase 4, Milestone 3 | Data-health dashboard and final tests | ⬜ |

## Daily workflow

1. Read the milestone scope and avoid starting the next milestone early.
2. Implement the smallest complete deliverable.
3. Run relevant unit tests and a Streamlit smoke test.
4. Update the milestone status and both Current sections.
5. Record decisions and limitations in the documentation.
6. Commit with a message naming the completed feature.

## Definition of done

A milestone is complete when its behavior works, edge cases fail safely, tests
cover its logic, UI language is accurate, and documentation is updated. The
milestone should be independently demonstrable before moving to the next one.
