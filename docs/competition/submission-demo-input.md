# Submission Demo Input Capture

Source URL: `https://www.kaggle.com/code/ryanholbrook/nvidia-nemotron-submission-demo/input`

Capture date: `2026-03-22`

Capture method: user-pasted content from the Kaggle notebook input page for Ryan Holbrook's `NVIDIA Nemotron Submission Demo`.

## Notebook Metadata Seen On The Page

- Notebook: `NVIDIA Nemotron Submission Demo`
- Author: `Ryan Holbrook`
- Relative page age in paste: `7d ago`
- Views shown in paste: `8,173`
- Model tag: `Nemotron-3-Nano-30B-A3B-BF16`
- Metric tag: `Kaggle Competition Metrics`
- Version tag: `V1 · Transformers · default`

## Competition Text Captured From The Page

### About this Competition

`Advance reasoning techniques using NVIDIA Nemotron open models on a novel benchmark`

`This dataset comprises a collection of logical reasoning puzzles requiring the identification and application of underlying transformation rules. The puzzles cover various domains, such as bit manipulation and algebraic equations.`

### File and Field Information

`train.csv`

- `id` - A unique identifier for each puzzle.
- `prompt` - The puzzle description, including input-output examples and the specific instance to be solved.
- `answer` - The ground truth solution for the puzzle.

`test.csv`

- `id` - A unique identifier for each puzzle.
- `prompt` - As in `train.csv`.

### Submission Format Signal

Exact line captured from the page:

`Note that your submission must be a file submission.zip containing a LoRA adapter. See the Evaluation page for details.`

## Attached Inputs Visible In The Paste

### Competition Data

- `train.csv`
- `test.csv`

### Utility / Runtime Inventory Signals

The pasted page also showed a large input inventory containing offline runtime packages and compiled libraries. Representative entries from the paste:

- `causal_conv1d-1.6.1.dist-info/...`
- `causal_conv1d_cuda.cpython-312-x86_64-linux-gnu.so`
- `flash_attn-2.8.3.dist-info/...`
- `flash_attn/...`
- `cuda_bindings-12.9.4.dist-info/...`
- `cuda_pathfinder-1.2.2.dist-info/...`
- `cuda_toolkit-12.8.1.dist-info/...`
- `PIL/...`
- `bin/torchrun`
- `bin/transformers`
- `bin/ninja`

This is useful as evidence that the demo environment is designed around an attached offline package/runtime bundle rather than a bare Kaggle image.

## What This Capture Confirms

- The competition notebook path expects a `submission.zip`.
- The submission artifact must contain a LoRA adapter.
- The notebook input page itself points users to the Evaluation page for the authoritative submission details.
- The sample test set is only for authoring submissions; scored runs replace it with a hidden test set of several hundred problems.

## What This Capture Does Not Yet Confirm

- Exact Evaluation-page runtime settings
- Exact adapter file contents required inside `submission.zip`
- Final hidden-test metric details
- Any official policy on external APIs or extra model assets

## Notes

- This is a partial official capture from the Kaggle notebook input page, not the full competition `Evaluation` or `Rules` page.
- The pasted inventory was very large; this file keeps the high-signal facts plus representative package entries instead of mirroring the full package tree.
