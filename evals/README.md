# Evaluation Guide

`cases.json` is the public evaluation dataset. It intentionally contains no API
key, resume, user profile, or complete prompt. The offline test suite validates
its schema and deterministic scorer:

```bash
python -m unittest tests.test_evaluation -v
```

For a live evaluation, run each question against the configured dashboard model,
record only the answer, visible tool names, citation count, groundedness result,
and scope-safety result, then pass that observable record to
`score_evaluation_result`. Do not record private candidate content.

`baseline.md` documents the pre-live deterministic baseline and the 10-point
human rubric. Save live runs as new dated files so model and dataset changes can
be compared without rewriting the original baseline.
