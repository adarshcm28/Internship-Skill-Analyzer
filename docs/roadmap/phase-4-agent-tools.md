# Phase 4 — Internship Agent Tools

## Goal

Give the Internship Assistant a small set of typed, read-only tools so it can
answer richer questions while the application—not the model—performs searching,
comparison, and aggregation.

## Milestone 1 — Internship search tool ⬜

**Day 8 deliverable:** A validated function tool for searching collected jobs.

- Define filters for company, title, US location, skills, difficulty, and minimum
  skill overlap.
- Execute searches against the processed project dataset only.
- Return a capped list with stable identifiers, match evidence, and source URLs.
- Validate values and return a useful empty-result response.
- Test each filter, combined filters, result limits, and malformed arguments.

## Milestone 2 — Internship comparison tool ⬜

**Day 9 deliverable:** A function tool that compares up to three postings.

- Accept stable posting identifiers rather than free-form job text.
- Calculate shared, unique, matched, and missing skills deterministically.
- Include company, role, location, and source links in the result.
- Prevent comparison of missing or duplicate identifiers.
- Test ordering, incomplete records, and two- and three-posting comparisons.

## Milestone 3 — Market-insights tool ⬜

**Day 10 deliverable:** A function tool for trustworthy dataset summaries.

- Support counts, top skills, category distribution, and difficulty distribution.
- Apply active dashboard filters before calculating aggregates.
- Return both values and the number of postings behind each result.
- Keep arithmetic in pandas or project functions rather than asking the model to
  calculate from prose.
- Test filtered totals, ties, missing categories, and empty datasets.

## Milestone 4 — Multi-tool orchestration and traces ⬜

**Day 11 deliverable:** A bounded tool loop that visibly explains which tools
supported an answer.

- Create an allowlisted dispatcher for the three read-only tools.
- Support multiple tool calls while enforcing a maximum call count.
- Reject unknown tools and malformed output without crashing the app.
- Show a compact “How this answer was produced” trace without exposing hidden
  instructions or sensitive data.
- Test single-tool, multi-tool, repeated-tool, and tool-failure conversations.

## Phase exit criteria

The agent can select and combine safe project tools, while every data claim can
be traced to a deterministic result and a known set of postings.
