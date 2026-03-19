---
name: temporal-ml-orchestrator
description: Design and operate durable Temporal workflows for model evaluation, prompt sweeps, reranking, synthetic-data generation, and continuous search. Use when Codex needs to add or modify Temporal workflows, activities, worker wiring, retry behavior, fan-out patterns, or artifact handoff between long-running ML jobs.
---

# Temporal ML Orchestrator

## Quick Start

- Keep workflow code deterministic.
- Push network calls and filesystem writes into activities.
- Store enough identifiers in run provenance to resume or audit work later.
- Prefer fan-out by run id or manifest id, not by passing large payloads through workflow history.

## Workflow Rules

- Workflows decide order and retries.
- Activities perform the real side effects.
- API routes queue work; workers execute it.
- Inline execution may exist for local development, but Temporal remains the durable path.

## Resources

- Read `references/patterns.md` for the repo’s default workflow boundaries.
- Run `scripts/print_env_contract.py` to show the worker env contract before deployment.
