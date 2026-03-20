# Kaggle Offline Runtime Plan

The RTX Pro 6000 Kaggle notebook path may block internet access for this competition. When that happens, the notebook must install all required packages from attached inputs instead of PyPI.

## Required Offline Wheelhouse Contents

Attach a Kaggle dataset that contains Linux Python 3.12 wheels for:

- `torch`
- `torchvision`
- `torchaudio`
- `mamba-ssm`
- `causal-conv1d`
- `ninja`
- `packaging`

If the Blackwell GPU still requires a newer CUDA build than Kaggle ships by default, the wheelhouse must include a Torch build compatible with that accelerator.

PyPI package pages for `mamba-ssm` and `causal-conv1d` currently document source-based installation and may not provide ready-made wheels for every target environment. In practice, that means you may need to build the wheels in a compatible Linux/CUDA environment first, then upload the finished wheelhouse as a Kaggle dataset.

## Notebook Behavior

`notebooks/nemotron_leaderboard_engine.ipynb` now:

- scans `/kaggle/input` for `.whl` files,
- detects candidate wheelhouse directories,
- prefers offline wheel installs when a matching wheelhouse is attached,
- and only falls back to online installs when internet is actually available.

## Operational Loop

1. Build or upload the wheelhouse as a Kaggle dataset.
2. Attach the wheelhouse dataset to the competition notebook.
3. Run the notebook from the top.
4. Export the resulting run bundle from `/kaggle/working`.
5. Import it locally with `make kaggle-import SOURCE=/path/to/kaggle_run_<run_id>.zip`.
