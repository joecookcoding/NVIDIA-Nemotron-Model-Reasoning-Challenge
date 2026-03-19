---
name: nemotron-experiment-flywheel
description: Run and refine the Nemotron experiment loop for prompt search, reasoning-budget sweeps, self-consistency, ranking, reranking, and candidate promotion. Use when Codex needs to create or compare experiment specs, expand prompt variants, interpret run artifacts, or decide which run should advance toward submission.
---

# Nemotron Experiment Flywheel

## Quick Start

- Start from a baseline experiment and freeze the exact benchmark, provider, model, seed, and prompt template.
- Expand only one major variable at a time: prompt variant, reasoning mode, thinking budget, or reranker policy.
- Save candidate variants in repo-visible files before launching large sweeps.
- Promote only the best-scoring or best-justified variant into the next cycle.

## Default Loop

1. Establish a reproducible baseline.
2. Generate a sweep matrix for prompt and reasoning controls.
3. Run the sweep.
4. Inspect scores, latency, and candidate quality together.
5. Rerank or prune.
6. Turn the surviving configuration into the next cycle.

## Heuristics

- If prompt variants change multiple behaviors at once, split them into separate experiments.
- If the eval metric is still unofficial, rank by both score and decision quality, not score alone.
- If the prompt sweep widens faster than analysis can keep up, collapse the matrix and go narrower.
- Treat self-consistency and reranking as separate levers; do not hide them inside prompt changes.

## Resources

- Read `references/loop.md` for the standard experiment progression.
- Read `references/selection_policy.md` when deciding whether a run should advance.
- Run `scripts/build_sweep_matrix.py` to turn a compact JSON request into a repeatable set of prompt variants.
