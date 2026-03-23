# Competition Overview

Source URL: `https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge`

Capture date: `2026-03-22`

Capture method: user-pasted content from the authenticated Kaggle competition page.

## Tagline

`Advance reasoning techniques using NVIDIA Nemotron open models on a novel benchmark`

## Short Overview

`Develop techniques that improve reasoning accuracy using NVIDIA Nemotron models.`

`Participants will experiment with prompting, data pipelines, and lightweight fine-tuning while evaluating their approaches on a new reasoning benchmark developed by NVIDIA Research.`

## Description

The competition page states that:

- reasoning benchmarks are useful for measuring progress on structured tasks,
- a shared benchmark and common baseline model allow more consistent comparison,
- structured reasoning benchmarks remain an active area of research and optimization,
- participants work from a shared `Nemotron 3 Nano` baseline and a benchmark developed by NVIDIA Research,
- Nemotron provides openly available models, datasets, and training recipes,
- multiple valid solution paths are expected.

The page explicitly lists example approach categories:

- Prompting strategies
- Data filtering and curation
- Synthetic data generation
- Reinforcement learning
- Lightweight fine-tuning
- Or other approaches of your choice

It also explicitly states:

- participants may use any training framework, tooling, or workflow to produce their LoRA adapter,
- NVIDIA-provided recipes are optional starting points,
- competitors may use other ecosystems and libraries such as `Hugging Face`, `Unsloth`, `Axolotl`, `TRL`, or similar tooling,
- the only requirement is that the final submission produces a compatible LoRA adapter for the `Nemotron-3-Nano-30B` base model,
- public notebooks and write-ups are encouraged and required for prize eligibility.

## Timeline

- `2026-03-16` - Start Date
- `2026-04-09` - Midpoint Cut-off Date
- `2026-06-08` - Entry Deadline
- `2026-06-08` - Team Merger Deadline
- `2026-06-15` - Competition End Date and Final Submission Deadline

The page states all deadlines are at `11:59 PM UTC` unless otherwise noted.

## Prize Notes

### Final Leaderboard Prizes

- `1st Place` - `$25,000 + 5 DGX Sparks`
- `2nd Place` - `$15,000 + 2 DGX Sparks`
- `3rd Place` - `$5,000 + 1 DGX Spark`

The page also states:

- a total of eight `DGX Spark` systems are awarded based on final leaderboard placement,
- hardware may cascade to lower-ranked teams if a higher-ranked team has fewer eligible members or hardware restrictions apply,
- each eligible participant may receive at most one `DGX Spark`,
- only officially registered team members are eligible for hardware prizes.

### Open Progress Prize

- `Open Progress Prize` - `$5,000 + 1 DGX Spark`
- awarded to the highest leaderboard score as of `2026-04-09`
- methodology submissions cut-off date: `2026-04-16`
- winners announced during `Cloud NEXT (2026-04-22 to 2026-04-24)`

### Open Contribution Awards

The page lists three category awards:

- `Best Data/Synthetic Data Method` - `1 DGX Spark`
- `Best RL Method` - `1 DGX Spark`
- `Best Fine-tuning Method` - `1 DGX Spark`

It also states that only submissions in the top `10%` of the final leaderboard are considered for these awards.

## Compute Note

The competition page states that compute is powered by `NVIDIA Blackwell on Google Cloud`, specifically `G4 VMs` powered by `NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs`.
