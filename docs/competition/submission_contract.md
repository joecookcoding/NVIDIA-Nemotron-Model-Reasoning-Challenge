# Submission Contract

Official competition details captured from the Kaggle competition and data pages:

- Output file: `submission.zip`
- Submission contents: a compatible `LoRA` adapter for `NVIDIA Nemotron-3-Nano-30B`
- Rank cap: at most `32`
- Required adapter file signal: `adapter_config.json`
- Evaluation runtime: the base model is loaded with the submitted LoRA adapter using `vLLM`

## Confirmed Source Signals

- The competition page says: submit a LoRA adapter of rank at most `32` for the `NVIDIA Nemotron-3-Nano-30B` model packaged into `submission.zip`.
- The data page repeats that the submission must be `submission.zip` containing a LoRA adapter.
- The evaluation section states that the adapter must include `adapter_config.json`.

## Still Pending

- Exact required file list inside `submission.zip`
- Any directory structure requirements inside the zip
- Any hidden-test caveats beyond the public page text
- The exact relative numerical tolerance value from the metric page, which was missing in the pasted capture
