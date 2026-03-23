# Evaluation

Source URL: `https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge`

Capture date: `2026-03-22`

Capture method: user-pasted content from the authenticated Kaggle competition page.

## Metric Summary

The competition page states that submissions are evaluated on `Accuracy` in solving the provided tasks.

The evaluation flow captured from the page:

- `NVIDIA Nemotron-3-Nano-30B` is loaded with the submitted LoRA adapter
- the adapter must include `adapter_config.json`
- inference uses the `vLLM` engine
- for each test case, the model is prompted to generate a response
- the model is instructed to place its final answer inside `\boxed{}`
- the metric extracts the final answer from the generated text
- extraction prioritizes boxed content, then falls back to heuristic patterns or the last numeric value found
- a prediction is graded as correct if it matches the ground truth either exactly as a string or within a relative numerical tolerance

## Important Capture Gap

The pasted page text includes:

`within a relative numerical tolerance of`

but the tolerance value itself was missing from the paste. This file intentionally does not guess that number.

## Runtime Parameters Listed On The Page

| Parameter | Value |
| --- | --- |
| `max_lora_rank` | `32` |
| `max_tokens` | `7680` |
| `top_p` | `1.0` |
| `temperature` | `0.0` |
| `max_num_seqs` | `64` |
| `gpu_memory_utilization` | `0.85` |
| `max_model_len` | `8192` |

## Practical Implications

- final evaluation is not using a generic CSV prediction file
- the submitted artifact is a LoRA adapter package consumed by `vLLM`
- generation behavior is materially shaped by the listed runtime parameters
- answer formatting inside `\boxed{}` matters because the metric prioritizes boxed extraction
