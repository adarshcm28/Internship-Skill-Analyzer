# Phase 3 — Personalized AI Career Coach

## Goal

Connect the deterministic Personal Skill-Gap Analyzer to the Internship
Assistant so explanations and plans are personalized without asking the model to
guess match scores.

## Milestone 1 — Personalization context ✅

**Day 4 deliverable:** The assistant can explain results using the user's
selected skills and calculated matches.

- Create a small, typed representation of the user's selected skills.
- Pass deterministic match percentages, matched skills, and missing skills into
  the assistant context.
- Keep raw skill selections in the current session unless the user chooses a
  future persistence feature.
- Clearly distinguish calculated facts from model-generated guidance.
- Test profiles with no skills, complete matches, and unknown skills.

### What was implemented

- `src/personalization.py` defines a typed, session-only user profile, normalizes
  catalog skills, discloses ignored unknown values, and builds a deterministic
  summary of average and best overlap across visible postings.
- `src/retrieval.py` now includes each retrieved posting's application-calculated
  match percentage, matched skills, missing skills, and supporting counts.
- `app.py` passes the profile and verified calculations to the assistant only
  after a question is submitted, shows whether personalization is active, and
  resets conversation history when the selected skill profile changes.
- `src/chatbot.py` tells the model to preserve application-calculated values,
  explain them as catalog-skill overlap, and separate evidence-backed observations
  from general guidance or hiring predictions.
- `tests/test_personalization.py`, `tests/test_retrieval.py`, and
  `tests/test_chatbot.py` cover empty profiles, partial and complete matches,
  unknown skills, session scope, profile changes, and the separated model input.

## Milestone 2 — Skill-gap analysis tool ✅

**Day 5 deliverable:** A read-only function tool that gives the agent verified
skill-gap calculations.

- Define a strict `analyze_skill_gap` input and output schema.
- Reuse the existing deterministic skill-gap functions instead of duplicating
  calculations in the prompt.
- Validate tool arguments and reject unknown postings or skills safely.
- Return matched, missing, and prioritized skills with supporting counts.
- Add mocked tests for the function call, result submission, and invalid input.

### What was implemented

- `src/agent_tools.py` defines a strict, read-only `analyze_skill_gap` function
  schema that accepts only an exact posting ID. Selected skills come from trusted
  Streamlit session state rather than model-generated arguments.
- The handler validates the current dataset, posting ID uniqueness, catalog-backed
  profile skills, and the presence of a selected skill before reusing
  `calculate_skill_gap` from `src/skill_gap.py`.
- Success results contain company, role, match percentage, matched and missing
  skills, supporting counts, calculation method, and an interpretation warning.
  Invalid requests return structured error codes without changing any data.
- `src/chatbot.py` now advertises the strict tool to the Responses API, executes
  at most one allowlisted call, returns a `function_call_output`, and requires the
  follow-up response to explain the verified result without further tool calls.
- `app.py` provides only the visible postings and current session profile to the
  tool runner. `tests/test_agent_tools.py` and `tests/test_chatbot.py` cover the
  schema, dispatcher, calculations, errors, call limit, and two-request API loop
  entirely with mocks.

## Milestone 3 — Personalized learning plan 🚧

**Day 6 deliverable:** A structured, evidence-based learning plan.

- Define a stable response structure for goals, ordered skills, practice tasks,
  and a portfolio project.
- Ground priority choices in the tool's missing-skill frequencies.
- Let the user choose an available time horizon without claiming guaranteed
  readiness or hiring outcomes.
- Show which recommendations come from internship data and which are general
  coaching suggestions.
- Test empty gaps, short timelines, malformed model output, and fallback display.

## Milestone 4 — Job-specific coaching experience ⬜

**Day 7 deliverable:** A user can select a posting and receive an actionable
preparation plan in the dashboard.

- Add a clear “Ask Internship Assistant” action to a selected posting.
- Include the posting source, the user's skill profile, and verified match data.
- Display preparation steps, missing-skill explanations, and suggested questions
  to research before applying.
- Preserve chat state when dashboard filters rerun the Streamlit app.
- Add an end-to-end mocked test and update the user guide.

## Phase exit criteria

The assistant can explain an individual match and produce a structured learning
or application-preparation plan backed by deterministic project data.
