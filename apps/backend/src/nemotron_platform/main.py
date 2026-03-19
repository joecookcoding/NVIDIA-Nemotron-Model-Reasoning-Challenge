from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentRecord,
    HealthResponse,
    LeaderboardEntry,
    RunRecord,
    SubmissionBuildRequest,
    SubmissionBundle,
    SubmissionValidateRequest,
    SubmissionValidation,
    SyntheticDatasetManifest,
    SyntheticDatasetRequest,
)
from .runtime import RuntimeServices, get_runtime
from .services.orchestration import WorkflowLauncher, build_workflow_launcher


@dataclass(slots=True)
class AppState:
    runtime: RuntimeServices
    launcher: WorkflowLauncher


def create_app() -> FastAPI:
    runtime = get_runtime()
    launcher = build_workflow_launcher(runtime.settings, runtime.evaluation)

    app = FastAPI(title="Nemotron Competition Platform", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.stateful_services = AppState(runtime=runtime, launcher=launcher)

    def get_state() -> AppState:
        return app.state.stateful_services

    @app.get("/health", response_model=HealthResponse)
    async def health(state: AppState = Depends(get_state)) -> HealthResponse:
        return HealthResponse(
            status="ok",
            database_path=str(state.runtime.settings.database_path),
            artifacts_root=str(state.runtime.settings.artifacts_root),
            orchestrator_mode=state.runtime.settings.orchestrator_mode,
        )

    @app.get("/experiments", response_model=list[ExperimentRecord])
    async def list_experiments(state: AppState = Depends(get_state)) -> list[ExperimentRecord]:
        return state.runtime.repository.list_experiments()

    @app.post("/experiments", response_model=ExperimentCreateResponse)
    async def create_experiment(
        request: ExperimentCreateRequest,
        state: AppState = Depends(get_state),
    ) -> ExperimentCreateResponse:
        experiment = state.runtime.evaluation.create_experiment(request)
        run = state.runtime.evaluation.create_run_stub(
            experiment.id, request.workflow_kind, provenance={"trigger": "api"}
        )
        if request.auto_start:
            await state.launcher.launch(request.workflow_kind, run.id)
        return ExperimentCreateResponse(experiment=experiment, run=run)

    @app.get("/experiments/{experiment_id}")
    async def get_experiment(
        experiment_id: str, state: AppState = Depends(get_state)
    ) -> dict[str, object]:
        experiment = state.runtime.repository.get_experiment(experiment_id)
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found.")
        latest_run = (
            state.runtime.repository.get_run(experiment.latest_run_id)
            if experiment.latest_run_id
            else None
        )
        return {"experiment": experiment, "latest_run": latest_run}

    @app.get("/runs", response_model=list[RunRecord])
    async def list_runs(state: AppState = Depends(get_state)) -> list[RunRecord]:
        return state.runtime.repository.list_runs()

    @app.get("/runs/{run_id}", response_model=RunRecord)
    async def get_run(run_id: str, state: AppState = Depends(get_state)) -> RunRecord:
        run = state.runtime.repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return run

    @app.get("/leaderboards", response_model=list[LeaderboardEntry])
    async def get_leaderboard(
        state: AppState = Depends(get_state),
    ) -> list[LeaderboardEntry]:
        return state.runtime.repository.list_leaderboard()

    @app.get("/datasets", response_model=list[SyntheticDatasetManifest])
    async def list_datasets(
        state: AppState = Depends(get_state),
    ) -> list[SyntheticDatasetManifest]:
        return state.runtime.repository.list_dataset_manifests()

    @app.post("/datasets/synthetic", response_model=SyntheticDatasetManifest)
    async def build_synthetic_dataset(
        request: SyntheticDatasetRequest,
        state: AppState = Depends(get_state),
    ) -> SyntheticDatasetManifest:
        return state.runtime.synthetic.generate_dataset(request)

    @app.get("/submissions", response_model=list[SubmissionBundle])
    async def list_submissions(
        state: AppState = Depends(get_state),
    ) -> list[SubmissionBundle]:
        return state.runtime.repository.list_submissions()

    @app.post("/submissions/validate", response_model=SubmissionValidation)
    async def validate_submission(
        request: SubmissionValidateRequest,
        state: AppState = Depends(get_state),
    ) -> SubmissionValidation:
        return state.runtime.submissions.validate_submission(request)

    @app.post("/submissions/build", response_model=SubmissionBundle)
    async def build_submission(
        request: SubmissionBuildRequest,
        state: AppState = Depends(get_state),
    ) -> SubmissionBundle:
        return state.runtime.submissions.build_submission(request)

    return app


app = create_app()
