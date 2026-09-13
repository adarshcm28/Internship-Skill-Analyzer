# Phase 5 — Private Candidate Profile

## Goal

Let users privately review application materials, compare verified skills with
collected internships, and request carefully scoped writing guidance.

## Milestone 1 — Secure upload and local extraction ✅

**Day 12 deliverable:** Accept PDF, DOCX, and TXT application documents.

### What was implemented

- `src/candidate_profile.py` validates the extension, file signature, UTF-8 text,
  non-empty content, and a 5 MB maximum before parsing.
- PDF extraction uses `pypdf`; DOCX extraction uses `python-docx`, including
  paragraphs and tables; TXT content is decoded locally. Extracted text is
  cleaned and bounded to 50,000 characters.
- `app.py` provides a session-only uploader and clearly explains that image-only
  scans and password-protected PDFs are not supported.
- Original file bytes are not placed in session state, saved to disk, committed,
  or sent to the API.

## Milestone 2 — Candidate profile review and editing ✅

**Day 13 deliverable:** Users verify the information used by the application.

### What was implemented

- Detected catalog skills are shown in an editable selector rather than treated
  as unquestioned facts.
- Editable fields cover summary, education, experience, projects, portfolio
  links, preferred roles, preferred US locations, and work authorization.
- `build_candidate_profile` normalizes skills and bounds every reviewed field
  before it can be used for matching or optional AI guidance.

## Milestone 3 — Resume-to-internship matching ✅

**Day 14 deliverable:** Deterministically rank visible internships for the profile.

### What was implemented

- `match_candidate_to_posting` reuses the catalog-backed skill-gap calculation
  for matched skills, missing skills, supporting counts, and overlap percentage.
- `rank_candidate_matches` ranks the currently filtered internship selection and
  displays the ten strongest matches in the Candidate Profile interface.
- The UI labels the calculation as a navigation aid rather than an eligibility
  score or hiring prediction.

## Milestone 4 — Tailored resume and cover-letter guidance ✅

**Day 15 deliverable:** Generate grounded application-writing assistance.

### What was implemented

- Users choose a specific visible internship and either resume suggestions or a
  cover-letter draft.
- Only reviewed profile fields, bounded posting evidence, and the deterministic
  match are included in the OpenAI request after explicit consent.
- Instructions prohibit invented education, experience, credentials, metrics,
  authorization, and company interest. Missing facts must remain placeholders.
- Responses use `store=False` and have a bounded output length.

## Milestone 5 — Privacy controls and testing ✅

**Day 16 deliverable:** Give users control over personal application information.

### What was implemented

- A **Delete uploaded data** action removes the extracted document, reviewed
  fields, target selection, consent state, and generated guidance, then resets
  the uploader.
- Consent is required at the moment AI guidance is requested; document upload,
  review, and deterministic matching do not call OpenAI.
- `tests/test_candidate_profile.py` covers TXT and DOCX extraction, malicious or
  invalid files, size limits, normalization, matching, ranking, stateless API
  requests, invalid guidance modes, and complete session deletion.

## Phase exit criteria

Users can upload, verify, match, and delete their application data while optional
AI assistance remains transparent, bounded, stateless, and user initiated.
