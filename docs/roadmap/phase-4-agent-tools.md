# Phase 4 — Internship Agent Tools

## Goal

Give the Internship Assistant a small set of typed, read-only tools so it can
answer richer questions while the application—not the model—performs searching,
comparison, and aggregation.

## Milestone 1 — Internship search tool ✅

**Day 8 deliverable:** A validated function tool for searching collected jobs.

- Define filters for company, title, US location, skills, difficulty, and minimum
  skill overlap.
- Execute searches against the processed project dataset only.
- Return a capped list with stable identifiers, match evidence, and source URLs.
- Validate values and return a useful empty-result response.
- Test each filter, combined filters, result limits, and malformed arguments.

### What was implemented

- `src/agent_tools.py` defines a strict `search_internships` function tool with
  nullable company, title, US location, difficulty, and overlap filters, a
  catalog-backed skills list, and a 1–10 result limit.
- The handler searches only the scored postings supplied from the active
  dashboard selection. Filtering and overlap calculations happen in pandas and
  the deterministic skill-gap module—not in model-generated prose.
- Results include stable posting IDs, roles, companies, locations, detected and
  matched skills, difficulty, overlap, and validated source URLs. Empty searches
  return a successful zero-result contract; invalid inputs return safe errors.
- `src/chatbot.py` exposes both read-only tools through strict schemas and keeps
  the current one-tool-per-answer limit until the multi-tool milestone.
- `tests/test_agent_tools.py` covers individual and combined filters, overlap,
  limits, empty results, malformed values, strict schema rules, and dispatch.

## Milestone 2 — Internship comparison tool ✅

**Day 9 deliverable:** A function tool that compares up to three postings.

- Accept stable posting identifiers rather than free-form job text.
- Calculate shared, unique, matched, and missing skills deterministically.
- Include company, role, location, and source links in the result.
- Prevent comparison of missing or duplicate identifiers.
- Test ordering, incomplete records, and two- and three-posting comparisons.

### What was implemented

- `src/agent_tools.py` adds a strict `compare_internships` tool accepting only
  two or three unique posting IDs from the active dashboard selection.
- The handler preserves the requested order and calculates shared skills, skills
  unique to each role, and each role's matched and missing profile skills with
  the existing deterministic skill-gap functions.
- Results include the company, role, location, validated source link, and the
  catalog-overlap limitation. Missing IDs, duplicate request IDs, and duplicate
  dataset IDs return structured errors instead of partial comparisons.
- `tests/test_agent_tools.py` covers two- and three-role comparisons, ordering,
  optional missing fields, deterministic calculations, and invalid identifiers.

## Milestone 3 — Market-insights tool ✅

**Day 10 deliverable:** A function tool for trustworthy dataset summaries.

- Support counts, top skills, category distribution, and difficulty distribution.
- Apply active dashboard filters before calculating aggregates.
- Return both values and the number of postings behind each result.
- Keep arithmetic in pandas or project functions rather than asking the model to
  calculate from prose.
- Test filtered totals, ties, missing categories, and empty datasets.

### What was implemented

- `src/agent_tools.py` adds a strict `market_insights` tool supporting selection
  counts, top skills, skill-category distribution, and difficulty distribution.
- Every calculation runs over the DataFrame supplied by the current Streamlit
  filters. Results report the supporting selection size, use unique posting
  counts, and sort ties alphabetically for repeatable output.
- Skill categories come from the project's canonical `SKILL_CATALOG`; no model
  arithmetic or invented category mapping is used.
- Tests cover filtered counts, deterministic ties, both distributions, schema
  validation, and a successful empty-dataset result.

## Milestone 4 — Multi-tool orchestration and traces ✅

**Day 11 deliverable:** A bounded tool loop that visibly explains which tools
supported an answer.

- Create an allowlisted dispatcher for the three read-only tools.
- Support multiple tool calls while enforcing a maximum call count.
- Reject unknown tools and malformed output without crashing the app.
- Show a compact “How this answer was produced” trace without exposing hidden
  instructions or sensitive data.
- Test single-tool, multi-tool, repeated-tool, and tool-failure conversations.

### What was implemented

- `src/chatbot.py` now advertises the skill-gap, search, comparison, and market
  tools through one allowlist and supports a maximum of four calls over three
  rounds before requiring a final answer.
- Identical calls are blocked, malformed and unknown requests receive safe tool
  results, parallel calls remain disabled, and all tools remain read-only.
- `answer_question_with_trace` returns the answer with a sanitized trace that
  contains only tool name, completion status, and a short result summary. It
  excludes tool arguments, hidden instructions, credentials, and profile skills.
- `app.py` stores the trace with each assistant message and displays it inside a
  **How this answer was produced** section that survives normal Streamlit reruns.
- Mocked tests cover existing single-tool behavior, multiple tools, repeated-call
  blocking, result submission, and secret-free trace content without live API use.

## Phase exit criteria

The agent can select and combine safe project tools, while every data claim can
be traced to a deterministic result and a known set of postings.
