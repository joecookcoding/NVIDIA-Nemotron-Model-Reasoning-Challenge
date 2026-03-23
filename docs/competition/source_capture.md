# Kaggle Source Capture

This repo still needs the exact Kaggle competition text copied from the authenticated competition page.

## Capture Status

- `Overview`: captured from the competition page
- `Evaluation`: captured from the competition page, except the pasted tolerance value is incomplete
- `Rules`: captured from the pasted rules page
- `Submission file format`: captured from the competition and data pages
- `Notebook/runtime limits`: partial - evaluation parameters and demo runtime bundle are captured, but full notebook/network rules are still pending
- `External model/API usage policy`: partial - rules allow external data and tools subject to reasonableness and accessibility

## Captured Sources

- `docs/competition/submission-demo-input.md` - user-pasted capture of the Kaggle `NVIDIA Nemotron Submission Demo` input page on `2026-03-22`
- `docs/competition/overview.md` - user-pasted capture of the main competition page on `2026-03-22`
- `docs/competition/evaluation.md` - evaluation details captured from the main competition page on `2026-03-22`
- `docs/competition/data.md` - user-pasted capture of the competition data page on `2026-03-22`
- `docs/competition/discussion-681745.md` - resource discussion capture on `2026-03-22`
- `docs/competition/rules.md` - user-pasted capture of the Kaggle rules page on `2026-03-22`

## Required Next Step

Paste or transcribe the competition page content into the sections below without paraphrasing the official constraints.

## Overview Snapshot

Captured from the main competition page:

- `Advance reasoning techniques using NVIDIA Nemotron open models on a novel benchmark`
- participants may use any training framework, tooling, or workflow to produce their LoRA adapter
- the final requirement is a compatible LoRA adapter for the `Nemotron-3-Nano-30B` base model

## Evaluation Snapshot

Captured from the main competition page:

- evaluation metric is `Accuracy`
- the submitted LoRA adapter is loaded into `NVIDIA Nemotron-3-Nano-30B` with `vLLM`
- the adapter must include `adapter_config.json`
- the model is instructed to put the final answer inside `\boxed{}`
- page-listed parameters include `max_lora_rank=32`, `max_tokens=7680`, `temperature=0.0`, `top_p=1.0`, `max_num_seqs=64`, `gpu_memory_utilization=0.85`, `max_model_len=8192`
- the pasted tolerance line is incomplete and still needs a cleaner capture

## Rules Snapshot

Captured from the rules page:

- max team size is `5`
- max submissions per day is `5`
- up to `2` final submissions may be selected
- external data and tools are allowed if publicly accessible at no cost or satisfy the `Reasonableness` standard
- private sharing outside teams is not permitted
- prize eligibility requires a public Kaggle notebook and solution write-up
- competition data is under `CC BY 4.0` and use must acknowledge the `NVIDIA Research team`

## Notes

- Public sources confirm the challenge is about improving Nemotron reasoning performance, but they do not replace the Kaggle rules.
- Current official captures confirm that the submitted artifact is `submission.zip` containing a LoRA adapter for `NVIDIA Nemotron-3-Nano-30B`.
- Do not finalize submission packaging, external API strategy, or notebook runtime assumptions until this file is completed.
