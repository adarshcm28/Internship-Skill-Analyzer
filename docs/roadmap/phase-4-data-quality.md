# Phase 4 — Data Quality and Posting Freshness

## Goal

Make collector health and listing freshness visible so users and interviewers can
judge the reliability of the dataset.

## Milestones

### ⬜ Milestone 1 — Produce collection diagnostics — Day 12

- Count boards attempted, successful, empty, and failed.
- Count exclusions by reason: role, internship evidence, US evidence, missing
  data, duplicate URL, and company cap.
- Write a timestamped structured run report without exposing credentials.
- Test counters and partial provider failures.

Done when every collector run explains what was accepted and rejected.

### ⬜ Milestone 2 — Track posting freshness — Day 13

- Define stable identity using provider and external ID.
- Record first seen, last seen, and consecutive missed runs.
- Define active, possibly closed, and closed statuses conservatively.
- Preserve history when a provider temporarily fails.
- Test new, recurring, missing, and returning postings.

Done when status changes are reproducible without treating one failed run as closure.

### ⬜ Milestone 3 — Add the data-health dashboard — Day 14

- Display last successful collection time and dataset age.
- Show provider and board success, warning, and failure counts.
- Show inclusion/exclusion reasons and posting-status totals.
- Label stale or uncertain data clearly in the opportunity view.
- Add UI tests, documentation, and an interview demonstration script.
- Update Current trackers and mark the roadmap complete.

Done when users can assess coverage, freshness, and collector reliability in the UI.
