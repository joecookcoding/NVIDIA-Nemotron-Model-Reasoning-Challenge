export type WorkflowKind =
  | "baseline_eval"
  | "prompt_sweep"
  | "rerank"
  | "synthetic_data"
  | "continuous_search";

export type RunStatus = "queued" | "running" | "succeeded" | "failed";

export type Experiment = {
  id: string;
  name: string;
  benchmark: string;
  provider: string;
  model: string;
  tags: string[];
  latest_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Run = {
  id: string;
  experiment_id: string;
  workflow_kind: WorkflowKind;
  status: RunStatus;
  aggregate_score: number | null;
  total_task_count: number;
  completed_task_count: number;
  latency_ms: number;
  cost_usd: number;
  decision_notes: string;
  updated_at: string;
};

export type LeaderboardEntry = {
  rank: number;
  experiment_id: string;
  experiment_name: string;
  run_id: string;
  workflow_kind: WorkflowKind;
  aggregate_score: number | null;
  benchmark: string;
  provider: string;
  model: string;
  tags: string[];
  updated_at: string;
};

export type DatasetManifest = {
  id: string;
  source_benchmark: string;
  provider: string;
  model: string;
  record_count: number;
  deduped_record_count: number;
  output_path: string;
  tags: string[];
  created_at: string;
};

export type SubmissionBundle = {
  id: string;
  experiment_id: string;
  run_id: string;
  version: string;
  status: "draft" | "valid" | "invalid";
  file_path: string;
  created_at: string;
  validation: {
    valid: boolean;
    issues: string[];
    warnings: string[];
  };
};

export type DashboardPayload = {
  experiments: Experiment[];
  runs: Run[];
  leaderboard: LeaderboardEntry[];
  datasets: DatasetManifest[];
  submissions: SubmissionBundle[];
};

