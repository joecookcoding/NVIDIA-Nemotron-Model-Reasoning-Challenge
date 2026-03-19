---
name: synthetic-data-curator
description: Generate, filter, deduplicate, and manifest synthetic reasoning data for Nemotron experiments. Use when Codex needs to expand a benchmark into synthetic tasks, curate JSONL records, add provenance tags, or apply a deterministic quality and dedupe pass before training or evaluation.
---

# Synthetic Data Curator

## Quick Start

- Generate synthetic records from a known benchmark or seed set.
- Keep provenance on every record.
- Deduplicate before scoring dataset quality.
- Reject records that change the task meaning or erase the expected answer format.

## Quality Rules

- Preserve answer format constraints.
- Preserve the original task intent unless the workflow explicitly targets adversarial augmentation.
- Reject trivial paraphrases that do not add a new reasoning pattern.
- Do not mix training-ready and eval-only synthetic records without tagging them separately.

## Workflow

1. Pick the source benchmark and scope.
2. Generate candidate records.
3. Deduplicate by normalized prompt or a stronger task key.
4. Run the quality rubric before persisting.
5. Emit a manifest with source, model, and filter counts.

## Resources

- Read `references/quality_rubric.md` before accepting a dataset.
- Run `scripts/dedupe_jsonl.py` on JSONL files when the generation loop produces near-duplicates.
