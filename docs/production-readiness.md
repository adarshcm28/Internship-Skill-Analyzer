# Production Readiness and Responsible AI Controls

## Status

The project is ready for a local portfolio demonstration. It is not a hosted job
application service and does not submit applications or verify that listings are
still open.

## Implemented controls

| Area | Control |
| --- | --- |
| Secrets | The API key is loaded from ignored local configuration and never rendered. |
| API retention | Every Responses API request sets `store=False`. |
| User input | Chat questions are limited to 2,000 characters. |
| Conversation | Six recent messages, 2,000 characters each, and 8,000 total characters. |
| Retrieval | At most 12 postings, 700 description characters each, and 24,000 context characters. |
| Tool execution | Read-only allowlist, four-call maximum, three rounds, and duplicate blocking. |
| Generation | Assistant output is capped at 1,600 tokens; learning plans at 2,200 tokens. |
| Reliability | API calls use timeouts, one retry, and user-facing classified errors. |
| Uploads | PDF, DOCX, or UTF-8 TXT only; 5 MB maximum; signatures validated. |
| Candidate privacy | Local extraction, reviewed fields, explicit consent, session-only state, complete delete. |
| Prompt injection | Job and resume text are labeled untrusted and cannot redefine agent behavior. |
| Observability | Session-only latency, tool, citation, and token counts; no content logging. |

## Known limitations

- Job data is a dated snapshot from configured public company career feeds.
- Skill extraction uses a transparent keyword catalog and can miss synonyms.
- Skill overlap is not an eligibility score or hiring prediction.
- Image-only and password-protected PDFs are not supported.
- Complex resume layouts can produce imperfect extraction order.
- AI-generated guidance can be incomplete and must be reviewed by the user.
- Session data disappears when the Streamlit session ends; there are no accounts.

## Deployment checklist

1. Use a dedicated OpenAI project and server-side environment variable.
2. Add authentication before hosting for multiple users.
3. Use TLS and configure upload, memory, request-rate, and session limits.
4. Review the deployment provider's logs and retention settings.
5. Add malware scanning before accepting public uploads.
6. Run the offline suite and live evaluation rubric against the deployment model.
7. Display a current collection date and refresh or remove stale postings.

## Responsible demonstration

Use synthetic or personally owned resume content. Never upload another person's
application materials without permission. Explain that deterministic matching
supports navigation while the model provides optional writing assistance.
