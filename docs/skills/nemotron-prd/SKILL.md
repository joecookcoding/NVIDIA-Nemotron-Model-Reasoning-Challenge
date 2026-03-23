---
name: nemotron-prd
description: Create or update a Ralph-style `prd.json` for this NVIDIA Nemotron competition repo. Use when Codex needs to turn a feature, submission upgrade, notebook improvement, rules task, or experiment plan into small user stories with priorities, acceptance criteria, and `passes` status for iterative execution.
---

# Nemotron PRD

## Quick Start

- Read the official competition captures in `docs/competition/` before writing task stories that depend on rules, submission format, or evaluation behavior.
- Use this skill when there is no `prd.json` yet, when the active goal changed, or when the current task list is too large or vague.
- Write stories for one-context-window execution. If a story feels like a mini-project, split it.

## Workflow

1. Identify the single target outcome.
2. Choose a `branchName` that matches that outcome.
3. Break the work into ordered user stories.
4. Keep each story independently verifiable.
5. Save the task list as root-level `prd.json`.

## Story Rules

- Each story must be small enough to finish in one focused coding iteration.
- Each story must have explicit acceptance criteria.
- Each story must name the smallest meaningful deliverable, not a broad theme.
- Separate planning, implementation, validation, and promotion when they create different risks.
- Separate competition-rules capture from model-quality work.
- Separate notebook runtime stabilization from model-training changes.

## Default Fields

- `branchName`
- `objective`
- `userStories`

Each user story should include:

- `id`
- `title`
- `priority`
- `passes`
- `acceptanceCriteria`
- `checks`
- `notes`

## Nemotron-Specific Heuristics

- Add a story for rules capture before any rules-sensitive submission change.
- Add a story for notebook/runtime stabilization before chasing score.
- Add a story for packaging validation before spending submissions.
- Add a story for public notebook and write-up readiness if prize eligibility matters.
- If a story changes UI or notebook UX, include browser or manual verification in acceptance criteria.

## Resources

- Read `references/prd-json.md` for the recommended `prd.json` shape.
- Read `docs/competition/source_capture.md` for what is official versus still pending.
- Read `docs/competition/evaluation.md` and `docs/competition/rules.md` when a story touches submission runtime, external tools, or prize eligibility.
