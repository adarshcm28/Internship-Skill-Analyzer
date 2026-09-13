# Internship Assistant AI Roadmap

This roadmap builds on the completed Personal Skill-Gap Analyzer and the
existing Internship Assistant. The milestones are sized as daily,
independently demonstrable improvements to the assistant.

## Current

| Item | Status |
| --- | --- |
| Completed foundation | Phase 1 — Personal Skill-Gap Analyzer |
| Current phase | Phase 6 — Evaluation and Production Readiness |
| Last completed milestone | Phase 5, Milestone 5 — Privacy controls and testing |
| Current milestone | Phase 6, Milestone 1 — Evaluation dataset and test harness |
| Roadmap day | Day 17 of 19 |

Status: ✅ Complete · 🚧 Current · ⬜ Not started

## Existing agent baseline

The project already has an Internship Assistant that:

- reads the OpenAI API key from local configuration without placing it in the UI;
- sends bounded, dataset-grounded context through the Responses API;
- maintains a short conversation history and supports clearing the chat;
- reports configuration and request errors in the Streamlit interface; and
- uses mocked tests so routine testing does not make paid API calls.

The milestones below improve this baseline instead of rebuilding it.

## Phases

| Phase | Focus | Milestones | Days |
| --- | --- | ---: | ---: |
| [Phase 1](phase-1-skill-gap.md) | Personal Skill-Gap Analyzer (foundation) | 1–6 | Complete |
| [Phase 2](phase-2-agent-reliability.md) | Agent Reliability and Grounding | 1–3 | 1–3 |
| [Phase 3](phase-3-career-coach.md) | Personalized AI Career Coach | 1–4 | 4–7 |
| [Phase 4](phase-4-agent-tools.md) | Internship Agent Tools | 1–4 | 8–11 |
| [Phase 5](phase-5-candidate-profile.md) | Private Candidate Profile | 1–5 | 12–16 |
| [Phase 6](phase-6-evaluation-production.md) | Evaluation and Production Readiness | 1–3 | 17–19 |

## Nineteen-day schedule

| Day | Phase and milestone | Daily deliverable | Status |
| ---: | --- | --- | :---: |
| 1 | Phase 2, Milestone 1 | Safe configuration check and agent health status | ✅ |
| 2 | Phase 2, Milestone 2 | Tested retrieval and citation context builder | ✅ |
| 3 | Phase 2, Milestone 3 | Modular instructions and safer conversations | ✅ |
| 4 | Phase 3, Milestone 1 | Skill profile and match data in agent context | ✅ |
| 5 | Phase 3, Milestone 2 | Skill-gap analysis function tool | ✅ |
| 6 | Phase 3, Milestone 3 | Structured personalized learning plan | ✅ |
| 7 | Phase 3, Milestone 4 | Job-specific coaching in the dashboard | ✅ |
| 8 | Phase 4, Milestone 1 | Internship search function tool | ✅ |
| 9 | Phase 4, Milestone 2 | Internship comparison function tool | ✅ |
| 10 | Phase 4, Milestone 3 | Market-insights function tool | ✅ |
| 11 | Phase 4, Milestone 4 | Safe multi-tool orchestration and traces | ✅ |
| 12 | Phase 5, Milestone 1 | Secure resume upload and local extraction | ✅ |
| 13 | Phase 5, Milestone 2 | Candidate profile review and editing | ✅ |
| 14 | Phase 5, Milestone 3 | Resume-to-internship matching | ✅ |
| 15 | Phase 5, Milestone 4 | Tailored resume and cover-letter guidance | ✅ |
| 16 | Phase 5, Milestone 5 | Privacy controls and testing | ✅ |
| 17 | Phase 6, Milestone 1 | Agent evaluation dataset and test harness | 🚧 |
| 18 | Phase 6, Milestone 2 | Safety, privacy, reliability, and cost controls | ⬜ |
| 19 | Phase 6, Milestone 3 | Observability, demo flow, and final documentation | ⬜ |

## Daily workflow

1. Read only the current milestone and keep the implementation within its scope.
2. Build the smallest complete version of its daily deliverable.
3. Test deterministic logic locally and mock OpenAI calls by default.
4. Make a live API request only when the milestone specifically requires it.
5. Update both Current sections and add **What was implemented** beneath the
   completed milestone.
6. Commit the milestone as one reviewable unit.

## Definition of done

A milestone is complete when it has a visible or testable result, handles its
expected failure cases, protects secrets and user data, includes proportionate
tests, and updates the relevant documentation. Claims made by the assistant must
be traceable to project data or clearly labeled as general guidance.

Only completed milestones receive implementation notes. Planned and current
milestones describe intended work and must not claim that code already exists.
