# Ralph Loop Reference

This skill adapts the public `snarktank/ralph` pattern to this repo's Codex workflow.

## Core Ralph Concepts

- each iteration starts with fresh context
- memory persists through git history, task state, and progress logs
- the loop succeeds only if stories are small
- quality checks are mandatory
- reusable learnings should be written down

## Memory Mapping For This Repo

Ralph repo concept -> This repo

- `prd.json` -> root `prd.json`
- `progress.txt` -> root `progress.txt`
- repo instructions -> `Codex.md`
- rules memory -> `docs/competition/*.md`

## Progress Log Format

Append, never replace:

```md
## Codebase Patterns

- Example: Submission packaging assumptions live in docs/competition/submission_contract.md
- Example: Evaluation parameters must follow docs/competition/evaluation.md

## 2026-03-22T14:30:00Z - S2

- Implemented: synced the Kaggle competition captures into docs/competition
- Files changed: docs/competition/source_capture.md, docs/competition/evaluation.md
- Checks run: manual doc readback
- Learnings for future iterations:
  - The final artifact is submission.zip, not a CSV
  - The metric expects boxed answers
  - The pasted tolerance value is still missing and must not be guessed

---
```

## Story Sizing

Good one-iteration stories:

- capture one official Kaggle source page
- patch one notebook packaging or determinism issue
- add one focused validation check
- promote one candidate run with justification

Bad one-iteration stories:

- build the entire winning pipeline
- rewrite all notebooks
- run every experiment idea at once

## Stop Condition

When every story in `prd.json` has `passes: true`, stop the loop and produce:

- the completed task state
- the current best artifact location
- the remaining unknowns, if any

## Source Note

This reference is derived from the public Ralph repo workflow:

- README: `https://github.com/snarktank/ralph`
- fresh-context / `prd.json` / `progress.txt` model from the repo overview
- single-story iteration and progress logging adapted from the repo's agent instructions
