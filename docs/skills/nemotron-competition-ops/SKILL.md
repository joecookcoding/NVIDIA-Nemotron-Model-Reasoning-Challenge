---
name: nemotron-competition-ops
description: Capture and maintain the NVIDIA Nemotron Kaggle competition operating context. Use when Codex needs to freeze Kaggle overview/evaluation/rules content, update the compliance matrix, check submission assumptions, review leaderboard operating discipline, or keep the daily competition decision log aligned with the repo state.
---

# Nemotron Competition Ops

## Quick Start

- Update `docs/competition/source_capture.md` with exact Kaggle text before making any rules-sensitive changes.
- Reconcile `docs/competition/compliance_matrix.md` after each new source capture.
- Use `scripts/check_rules_freeze.py` to confirm the required competition documents exist before assuming a submission contract.
- Record strategy pivots in `docs/competition/daily_decision_log.md`.

## Workflow

1. Check whether Kaggle `Overview`, `Evaluation`, and `Rules` have been copied into the repo.
2. If any section is missing, stop treating submission assumptions as final.
3. Update the compliance matrix with direct evidence and unresolved questions.
4. Confirm whether external APIs, extra datasets, fine-tuning, and notebook runtime assumptions are actually allowed.
5. Only after that, change validation logic or submission builders.

## Operating Rules

- Prefer exact quotes or screenshots from Kaggle over paraphrase.
- Treat every unresolved rule as a blocker for final submission packaging, not for local experimentation.
- Keep the repo’s assumptions explicit. Hidden assumptions lose competitions.
- Separate “safe for local experiments” from “safe for Kaggle submission runtime.”

## References

- Read `references/checklist.md` for the default competition operations checklist.
- Read `references/leaderboard_protocol.md` when deciding whether a new run should be promoted or only logged.
- Run `scripts/check_rules_freeze.py` to verify the rule capture status from the repo.
