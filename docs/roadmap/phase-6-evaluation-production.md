# Phase 6 — Evaluation and Production Readiness

## Goal

Measure the Internship Assistant, address its operational risks, and package a
repeatable demonstration suitable for interviews.

## Milestone 1 — Evaluation dataset and test harness 🚧

**Day 17 deliverable:** A repeatable evaluation suite with a recorded baseline.

- Create representative questions for search, comparison, skill gaps, market
  insights, candidate matching, empty evidence, and out-of-scope requests.
- Include adversarial posting text and prompt-injection attempts.
- Score tool selection, citation correctness, groundedness, and response format.
- Use deterministic checks where possible and a documented human rubric where
  judgment is required.
- Save a baseline report without API keys or personal application content.

## Milestone 2 — Safety, privacy, reliability, and cost controls ⬜

**Day 18 deliverable:** Documented controls with tested failure behavior.

- Limit user input, context size, history, output length, and tool-call count.
- Add timeouts, bounded retries, and messages for rate limits and service errors.
- Keep tools read-only and allowlisted, and treat collected text as untrusted.
- Avoid logging secrets, full prompts, resumes, or private skill profiles.
- Record token usage when available and add a configurable per-request budget.
- Maintain a clear privacy and AI-limitations notice in the dashboard.

## Milestone 3 — Observability and interview demo ⬜

**Day 19 deliverable:** A production-readiness report and repeatable demo flow.

- Record latency, success/failure state, tool names, and citation counts without
  recording secret or private content.
- Add a compact diagnostics view for development and demonstrations.
- Run the evaluation suite and compare the final report with the baseline.
- Update the README and architecture map to show the complete agent lifecycle.
- Write an interview demo script covering personalization, tools, grounding,
  candidate privacy, safety, limitations, and one handled failure case.
- Complete a final Streamlit smoke test and document how to run the app.

## Phase exit criteria

The agent has measurable quality criteria, tested safety and failure controls,
useful operational signals, and an accurate interview demonstration.
