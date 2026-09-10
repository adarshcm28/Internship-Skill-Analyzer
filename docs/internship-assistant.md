# Internship Assistant Configuration and Health Check

## Purpose

The Internship Assistant uses the OpenAI Responses API to answer questions about
the postings currently selected in the dashboard. Its API key is read by the
Python application from local configuration and is never intentionally included
in prompts, dashboard state, or user-facing error messages.

## Local configuration

Create a `.env` file at the project root:

```text
OPENAI_API_KEY=your_actual_key
OPENAI_MODEL=gpt-5.6-luna
```

`.env` is excluded by `.gitignore`. Never paste the key into the assistant,
screenshots, source code, or Git commits. `OPENAI_MODEL` is optional; the app uses
its documented default when it is absent.

## Two levels of readiness

1. **Configured—not checked** means the app detected non-empty key and model
   settings. It does not prove that the key is valid.
2. **Agent ready** means the user selected **Check connection** and the API
   confirmed that the key can retrieve the configured model. This health check
   does not generate a model response.

The check runs only when requested so normal dashboard reruns do not repeatedly
contact the API.

## Grounded retrieval and citations

The assistant does not send every visible job description with every question.
After the user submits a question, `src/retrieval.py` performs a local,
deterministic search over the already-filtered dashboard data:

1. Extract up to 20 meaningful terms from the question.
2. Rank matches by job title, extracted skills, company, location, and description.
3. Remove duplicate posting identifiers and create a stable identifier when one
   is missing.
4. Keep only valid HTTP or HTTPS source URLs.
5. Include at most 12 postings, trim descriptions to 700 characters, and stop
   before the serialized JSON context exceeds 24,000 characters.
6. For a general question with no lexical match, include a small representative
   sample while preserving exact counts for the current dashboard selection.

Each retrieved posting contains a `citation_id` and `source_url`. The assistant's
instructions require job-specific claims to use `[citation_id](source_url)` and
forbid invented or altered citations. This is application-supplied Markdown
evidence, not a built-in web-search citation.

## Conversation safeguards

The request builder keeps five concerns separate:

1. Permanent system instructions define identity, supported scope, evidence
   rules, instruction safety, personalization rules, and response style.
2. Up to six recent valid chat messages preserve limited continuity, with a
   2,000-character limit per message and an 8,000-character combined limit.
3. Verified personalization JSON contains application-calculated facts.
4. Retrieved posting JSON contains untrusted evidence and citation metadata.
5. The current user question is the final, separately bounded message.

Posting descriptions, profile values, and user text cannot become system
instructions merely because they contain commands. The prompt tells the assistant
to disregard embedded directions, stay within internship-analysis scope, and say
when the provided evidence cannot support an answer.

## Personalized match context

When the user selects skills under **My Skills**, `src/personalization.py` creates
a typed profile marked `current_session_only`. It uses the existing deterministic
skill-gap functions to calculate average and best overlap across visible jobs.
The retrieved records also carry their exact match percentage, matched skills,
missing skills, matched count, and required count.

These numbers measure overlap with skills detected by this project's catalog.
They do not estimate eligibility, interview likelihood, or hiring probability.
The model receives instructions to explain these values without recalculating or
changing them. If the user has selected no skills, personalized matching is
explicitly marked unavailable.

## Skill-gap function tool

For questions about a particular job match, the Responses API can request the
read-only `analyze_skill_gap` function. Its strict public schema accepts one field:
the exact posting ID from retrieved evidence. It does not accept user skills from
the model. The application supplies those directly from the current Streamlit
session.

`src/agent_tools.py` then:

1. Rejects unknown tools and malformed or extra arguments.
2. Confirms that the posting ID exists exactly once in the visible selection.
3. Validates that the current profile contains supported catalog skills.
4. Calls the same deterministic `calculate_skill_gap` function used by the UI.
5. Returns matched skills, missing skills, percentage, counts, and calculation
   metadata as structured JSON.
6. Returns safe structured errors for invalid data without mutating the dataset.

The assistant performs at most one tool call per response during this milestone.
The tool result is returned as `function_call_output`, after which the model must
produce its final explanation with tool choice disabled. This is a deliberately
small orchestration loop; broader multi-tool behavior belongs to a later phase.

## Health states

| State | Meaning | Suggested action |
| --- | --- | --- |
| API key missing | No usable local key was detected | Add `OPENAI_API_KEY` and restart the app |
| Configured—not checked | Local settings exist but access is unverified | Select **Check connection** |
| Agent ready | Authentication and model access succeeded | Use the assistant |
| API access denied | The key is invalid or lacks permission | Check the API project and key |
| Model unavailable | The model does not exist or is not available to the project | Change `OPENAI_MODEL` or project access |
| Rate limit reached | The API temporarily rejected the request due to a limit | Wait and try again |
| Connection/service unavailable | The network or service is temporarily unavailable | Check connectivity and retry |
| API request failed | Another API request error occurred | Review billing, project settings, and access |

## Code map

- `chat_settings` in `src/chatbot.py` reads the key and model on the server.
- `configured_health` reports local readiness without contacting OpenAI.
- `check_agent_health` retrieves model metadata to validate access.
- `classify_openai_error` maps SDK exceptions to safe, actionable states and
  deliberately does not expose the original exception text.
- The Internship Assistant panel in `app.py` renders the status and connection
  button. Only secret-free status fields are saved in Streamlit session state.
- `tests/test_chatbot.py` replaces the OpenAI client with mocks so tests do not
  use a real key or make paid requests.
- `src/retrieval.py` selects question-relevant evidence, enforces context limits,
  and prepares citation metadata before any model request.
- `tests/test_retrieval.py` verifies ranking, bounds, deduplication, safe links,
  stable identifiers, empty inputs, and fallback behavior.
- `src/personalization.py` builds the typed session profile and verified match
  summary used in assistant requests.
- `build_response_input` in `src/chatbot.py` keeps bounded conversation,
  personalization, evidence, and the current question in distinct messages.
- `tests/test_personalization.py` covers empty, partial, complete, and invalid
  profiles without making API requests.
- `src/agent_tools.py` contains the strict tool schema, validated calculation,
  structured result contract, and allowlisted dispatcher.
- `tests/test_agent_tools.py` tests successful calculations and every validation
  error without contacting OpenAI.

## Security boundary

The dashboard is server-rendered, but the implementation still avoids storing the
key in Streamlit session state. Only the status name, label, message, readiness
boolean, and configured model name appear in the UI. A real chat request sends the
user's question, recent conversation, and bounded posting context to OpenAI; it
does not send the API key as prompt content.
