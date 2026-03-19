from __future__ import annotations

import json

from ..artifacts import ArtifactStore
from ..benchmarks import BenchmarkLoader
from ..models import SyntheticDatasetManifest, SyntheticDatasetRequest
from ..repository import SQLiteRepository


class SyntheticDataService:
    def __init__(
        self,
        repository: SQLiteRepository,
        artifact_store: ArtifactStore,
        benchmark_loader: BenchmarkLoader,
    ):
        self.repository = repository
        self.artifact_store = artifact_store
        self.benchmark_loader = benchmark_loader

    def generate_dataset(self, request: SyntheticDatasetRequest) -> SyntheticDatasetManifest:
        tasks = self.benchmark_loader.load(request.source_benchmark, request.limit)
        records: list[dict[str, object]] = []
        for task in tasks:
            for index in range(request.prompts_per_task):
                rewritten_prompt = (
                    f"Solve this carefully, then return the final answer only.\n\n{task.prompt}"
                    if index % 2 == 0
                    else f"Reason step by step internally, but respond briefly.\n\n{task.prompt}"
                )
                record = {
                    "synthetic_id": f"{task.task_id}-synth-{index + 1}",
                    "source_task_id": task.task_id,
                    "prompt": rewritten_prompt,
                    "reference_answer": task.reference_answer
                    if request.include_reference_answers
                    else None,
                    "provenance": {
                        "source_benchmark": request.source_benchmark,
                        "provider": request.provider,
                        "model": request.model,
                    },
                }
                records.append(record)

        deduped: dict[str, dict[str, object]] = {}
        for record in records:
            normalized = str(record["prompt"]).strip().casefold()
            deduped[normalized] = record

        manifest = SyntheticDatasetManifest(
            source_benchmark=request.source_benchmark,
            provider=request.provider,
            model=request.model,
            record_count=len(records),
            deduped_record_count=len(deduped),
            output_path="",
            manifest_path="",
            tags=request.tags,
        )

        jsonl_body = "\n".join(json.dumps(record) for record in deduped.values())
        output_path = self.artifact_store.write_text(
            "datasets", manifest.id, "synthetic.jsonl", jsonl_body
        )
        manifest.output_path = output_path
        manifest.manifest_path = self.artifact_store.write_json(
            "datasets", manifest.id, "manifest.json", manifest.model_dump(mode="json")
        )
        self.repository.save_dataset_manifest(manifest)
        return manifest
