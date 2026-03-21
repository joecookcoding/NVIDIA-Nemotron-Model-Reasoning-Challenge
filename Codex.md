# Codex Project Notes

## Commit Messages

When a repo change is ready and the user needs to commit it themselves, always provide a ready-to-use commit message in the response.

## Kaggle Notebook Installs

The Kaggle competition notebook runs offline. Keep `input_requirements.txt` limited to the pre-run install lines that work in Kaggle's dependency manager:

- `pip install --upgrade --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128`
- `pip install --upgrade transformers accelerate safetensors sentencepiece ninja packaging`

Do not add `mamba-ssm`, `causal-conv1d`, comments, blank lines, or `python -m pip` commands to `input_requirements.txt`.

The Kaggle notebook itself must not attempt network installs at runtime. It may perform local offline `pip install` steps from attached wheelhouse paths when needed.

Exception: `notebooks/nvidia-nemotron-sfttrainer-training.ipynb` is allowed to run a local offline `pip install` from the `dennisfong/nvidia-nemotron-offline-packages` wheelhouse. `notebooks/nemotron_leaderboard_engine.ipynb` is also allowed to install `mamba-ssm` and `causal-conv1d` from a detected offline wheelhouse. Neither notebook may call the public internet.
