# Nemotron Competition Platform

Competition-first internal platform for the NVIDIA Nemotron Model Reasoning Challenge.

## What Exists

- FastAPI control plane for experiments, runs, synthetic datasets, and submission bundles.
- SQLite-backed metadata store with filesystem artifact persistence.
- Provider abstraction with `openai-compatible` and `mock` backends.
- Temporal workflows and activities for baseline eval, prompt sweeps, reranking, synthetic data, and continuous search.
- Thin Vite 8 + React + Tailwind dashboard for queue, leaderboard, and submission visibility.
- Local competition skills under `docs/skills/`.

## Repo Layout

- `apps/backend`: FastAPI app, services, Temporal worker, tests.
- `apps/frontend`: Vite dashboard.
- `experiments`: benchmark samples and prompt templates.
- `notebooks`: Kaggle-facing starter notebooks and smoke tests.
- `artifacts`: generated outputs and submission bundles.
- `docs/competition`: Kaggle rules capture and compliance docs.
- `docs/skills`: reusable Codex skills for competition operations and experimentation.

## Quick Start

1. Copy `.env.example` to `.env` and set a hosted OpenAI-compatible endpoint if you want live inference.
2. Ensure the machine can create Python virtual environments. On Ubuntu/WSL this usually means `python3.12-venv` must be installed.
3. Default model target is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`, which exposes reasoning control through the chat template in NVIDIA's published examples.
4. Start the backend:

```bash
cd apps/backend
python3 -m uvicorn nemotron_platform.main:app --reload --app-dir src
```

5. Install the frontend dependencies:

```bash
bash -lc "source $HOME/.nvm/nvm.sh && npm install"
```

6. Start the dashboard:

```bash
bash -lc "source $HOME/.nvm/nvm.sh && npm run frontend:dev"
```

7. Optional: start the Temporal worker once a Temporal server is available:

```bash
cd apps/backend
python3 -m nemotron_platform.temporal.worker
```

## Current Gaps

- Kaggle `Overview`, `Evaluation`, and `Rules` still need to be frozen into `docs/competition/`.
- Docker and GPU are not required for v1, but local NIM/vLLM support is not wired yet.
- Submission validation currently defaults to a generic `id,answer` schema until the Kaggle format is captured.

## Nemotron Runtime Notes

- For local Kaggle-style inference, the primary model is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`.
- NVIDIA's published examples use `transformers` with `trust_remote_code=True`, `torch_dtype=torch.bfloat16`, and `device_map="auto"`.
- Reasoning-off mode should use the model's chat template flag rather than prompt hacks when the serving stack supports it.
- See `docs/competition/model_runtime_notes.md` for the working assumptions captured from the model references.

## Kaggle Notebook

- Competition notebook: `notebooks/nemotron_leaderboard_engine.ipynb`
- Use it for Kaggle-side GPU verification and model-load smoke tests before attempting full competition inference.
