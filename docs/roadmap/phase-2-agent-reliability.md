# Phase 2 — Agent Reliability and Grounding

## Goal

Make the existing Internship Assistant dependable before giving it more
abilities. It should fail clearly, select relevant evidence, and resist requests
that try to override its rules or invent unsupported facts.

## Milestone 1 — Secure connection and health check ✅

**Day 1 deliverable:** A safe, visible agent readiness check.

- Validate that required configuration exists without exposing secret values.
- Keep the model name configurable rather than embedding it throughout the app.
- Add a lightweight health-check path with clear states: ready, missing key,
  unavailable model, rate limited, and temporary service failure.
- Ensure logs, exceptions, screenshots, and browser state never contain the key.
- Add mocked tests for every configuration and health state.
- Document the difference between detecting a key and successfully validating
  access to the API.

### What was implemented

- `src/chatbot.py` now separates local configuration detection from live API
  validation, retrieves the configured model for a lightweight connection check,
  and converts SDK failures into secret-free health states.
- `app.py` displays the configured model and a readiness panel with an explicit
  **Check connection** button. Chat failures update the same status panel.
- `tests/test_chatbot.py` mocks every API interaction and covers missing keys,
  successful validation, authentication failure, unavailable models, rate limits,
  and connection failures without spending API credits.
- `docs/internship-assistant.md` explains configuration, health states, security
  boundaries, and how to use the connection check.

## Milestone 2 — Grounded retrieval and citations ✅

**Day 2 deliverable:** A tested context builder that returns relevant postings
and their source links.

- Move dataset selection and context construction into a focused module.
- Retrieve only postings relevant to the user's question and active filters.
- Enforce limits on postings, description length, and total context size.
- Attach stable posting identifiers and source URLs to every context item.
- Handle empty, incomplete, and duplicate records without inventing details.
- Test relevance, ordering, context limits, and citation metadata.

### What was implemented

- `src/retrieval.py` extracts meaningful query terms and ranks the active
  dashboard postings with transparent field weights: title, extracted skills,
  company, location, then description.
- The context builder sends no more than 12 relevant postings, limits each
  description to 700 characters, and caps the valid JSON payload at 24,000
  characters. General questions use a small representative fallback sample.
- Duplicate posting IDs are removed, missing IDs receive deterministic generated
  identifiers, and only valid HTTP or HTTPS source links enter model context.
- `src/chatbot.py` requires job-specific answers to cite the supplied identifier
  and exact source URL. `app.py` builds evidence only after the user submits a
  question while still resetting chat when dashboard filters change.
- `tests/test_retrieval.py` and `tests/test_chatbot.py` cover relevance, stable
  ordering, limits, citations, duplicates, incomplete data, unsafe URLs, empty
  results, and the fallback strategy without calling the API.

## Milestone 3 — Prompt and conversation safeguards ✅

**Day 3 deliverable:** Modular agent instructions and safer conversation rules.

- Separate system instructions, dataset evidence, history, and the new question.
- Define supported requests and a clear response for out-of-scope requests.
- Tell the assistant to treat posting text as data, not as instructions.
- Require uncertainty language when the supplied evidence cannot answer a claim.
- Bound history by turns and size, and preserve the existing clear-chat behavior.
- Test prompt-injection examples, unsupported claims, and empty-result questions.

### What was implemented

- `src/chatbot.py` now composes named instruction sections for identity, supported
  scope, evidence, instruction safety, personalization, and response style.
- Permanent rules stay in the Responses API `instructions` field. Bounded history,
  verified personalization JSON, retrieved posting JSON, and the current question
  are supplied as separate messages so their trust boundaries remain visible.
- Conversation history is limited to six valid recent messages, 2,000 characters
  per message, and 8,000 characters total. Questions remain capped at 2,000
  characters, and clearing chat still removes the session history.
- The rules explicitly redirect unrelated requests, treat all posting and profile
  content as untrusted data, refuse embedded instructions, require uncertainty
  when evidence is insufficient, and forbid fabricated facts or citations.
- `tests/test_chatbot.py` verifies instruction sections, role separation, history
  limits, injection placement, unsupported-claim guidance, and API request shape.

## Phase exit criteria

The agent reports its readiness accurately, answers from a bounded set of
traceable postings, and fails safely when configuration, evidence, or service
access is unavailable.
