import type {
  DashboardPayload,
  DatasetManifest,
  Experiment,
  LeaderboardEntry,
  Run,
  SubmissionBundle,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export async function fetchDashboardPayload(): Promise<DashboardPayload> {
  const [experiments, runs, leaderboard, datasets, submissions] = await Promise.all([
    fetchJson<Experiment[]>("/experiments"),
    fetchJson<Run[]>("/runs"),
    fetchJson<LeaderboardEntry[]>("/leaderboards"),
    fetchJson<DatasetManifest[]>("/datasets"),
    fetchJson<SubmissionBundle[]>("/submissions"),
  ]);

  return { experiments, runs, leaderboard, datasets, submissions };
}

