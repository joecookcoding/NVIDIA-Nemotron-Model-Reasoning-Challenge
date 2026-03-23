---
name: nemotron-ralph-loop
description: Run a Ralph-style fresh-context iteration loop in this NVIDIA Nemotron repo using `prd.json`, `progress.txt`, git history, and captured Kaggle docs. Use when Codex needs to pick the next small story, implement exactly one story, run checks, update progress, and prepare the next iteration without losing competition context.
---

# Nemotron Ralph Loop

## Quick Start

- Read root `prd.json`.
- Read root `progress.txt` if it exists. Start with the `Codebase Patterns` section.
- Read `Codex.md` and the relevant `docs/competition/` captures.
- If `prd.json` is missing or too vague, use the `nemotron-prd` skill first.
- If `progress.txt` is missing, create it with a `## Codebase Patterns` section and then append iteration logs.

## Default Loop

1. Pick the highest-priority story where `passes` is `false`.
2. Implement exactly one story.
3. Run the smallest relevant quality checks.
4. If checks pass, update the story to `passes: true`.
5. Append an iteration report to `progress.txt`.
6. Record durable learnings in `Codex.md` or the nearest durable repo doc when they are reusable.
7. Stop when all stories pass, then prepare the next submission candidate or promotion decision.

## Operating Rules

- One story per iteration.
- Keep changes focused and minimal.
- Do not hide multiple major levers inside one story.
- Prefer evidence-producing steps over speculative changes.
- Keep `progress.txt` append-only, except for maintaining the `Codebase Patterns` section near the top.

## Nemotron Competition Constraints

- Final submission artifact is `submission.zip`.
- The artifact must be a compatible LoRA adapter for `NVIDIA Nemotron-3-Nano-30B`.
- Rank must be at most `32`.
- Evaluation uses `vLLM` and expects `adapter_config.json`.
- Competition rules allow `5` submissions per day and up to `2` final submissions.
- Prize eligibility requires a public Kaggle notebook and a write-up.
- Private sharing outside the official Kaggle team is not allowed.

## Durable Memory

Use these as the loop's memory between iterations:

- git history
- `progress.txt`
- `prd.json`
- `docs/competition/` captures
- `Codex.md`

## When To Update Durable Docs

Update a durable doc only when the learning is reusable, for example:

- a packaging gotcha that will matter again
- a notebook runtime quirk
- a codebase convention
- an evaluation constraint from Kaggle

Do not write temporary debugging chatter into durable docs.

## Resources

- Read `references/loop.md` for the Ralph-to-Codex mapping and progress log format.
- Read `docs/competition/submission_contract.md` before changing submission packaging logic.
- Read `docs/competition/evaluation.md` before changing generation or adapter assumptions.
- Read `docs/competition/rules.md` before relying on external tools, external data, or prize workflows.
