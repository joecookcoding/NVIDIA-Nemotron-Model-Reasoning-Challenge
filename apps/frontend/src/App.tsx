import { startTransition, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { fetchDashboardPayload, getApiBaseUrl } from "./api";
import type { DashboardPayload, RunStatus } from "./types";

const EMPTY_DASHBOARD: DashboardPayload = {
  experiments: [],
  runs: [],
  leaderboard: [],
  datasets: [],
  submissions: [],
};

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function formatScore(score: number | null): string {
  if (score === null) {
    return "n/a";
  }
  return score.toFixed(4);
}

function statusTone(status: RunStatus): string {
  switch (status) {
    case "succeeded":
      return "bg-emerald-500/12 text-emerald-200 ring-1 ring-emerald-400/30";
    case "failed":
      return "bg-rose-500/12 text-rose-200 ring-1 ring-rose-400/30";
    case "running":
      return "bg-amber-500/12 text-amber-100 ring-1 ring-amber-400/30";
    default:
      return "bg-slate-500/12 text-slate-100 ring-1 ring-slate-400/30";
  }
}

function App() {
  const [payload, setPayload] = useState<DashboardPayload>(EMPTY_DASHBOARD);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const next = await fetchDashboardPayload();
        if (!cancelled) {
          startTransition(() => {
            setPayload(next);
            setIsLoading(false);
          });
        }
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : "Unknown dashboard error");
          setIsLoading(false);
        }
      }
    }

    void load();
    const intervalId = window.setInterval(() => void load(), 15000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const runningCount = payload.runs.filter((run) => run.status === "running").length;
  const queuedCount = payload.runs.filter((run) => run.status === "queued").length;
  const topScore = payload.leaderboard[0]?.aggregate_score ?? null;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_28%),linear-gradient(135deg,_#0f172a_0%,_#111827_45%,_#1f2937_100%)] text-slate-50">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/6 p-6 shadow-[0_30px_120px_rgba(0,0,0,0.35)] backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-amber-200/80">
                Nemotron Competition Ops
              </p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                Continuous experimentation for leaderboard pressure.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-200/80 sm:text-base">
                FastAPI runs the control plane, Temporal owns durable search workflows, and the
                dashboard stays focused on what matters: queue state, scores, prompt variants, and
                submission candidates.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Experiments" value={payload.experiments.length.toString()} />
              <StatCard label="Running" value={runningCount.toString()} />
              <StatCard label="Queued" value={queuedCount.toString()} />
              <StatCard label="Top Score" value={formatScore(topScore)} />
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 rounded-3xl border border-white/10 bg-slate-950/30 px-4 py-3 text-sm text-slate-200/75 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <span className="font-medium text-slate-100">API base:</span> {getApiBaseUrl()}
            </div>
            <div className="flex items-center gap-3">
              <span>{isLoading ? "Refreshing..." : "Auto-refresh every 15s"}</span>
              {error ? (
                <span className="rounded-full bg-rose-500/15 px-3 py-1 text-rose-200">
                  {error}
                </span>
              ) : null}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Panel title="Leaderboard">
            <div className="space-y-3">
              {payload.leaderboard.length === 0 ? (
                <EmptyState text="No leaderboard entries yet. Create an experiment and let the first run land." />
              ) : (
                payload.leaderboard.map((entry) => (
                  <article
                    key={entry.run_id}
                    className="rounded-3xl border border-white/8 bg-slate-950/35 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-slate-300/70">
                          Rank {entry.rank}
                        </p>
                        <h2 className="mt-2 text-lg font-semibold text-white">
                          {entry.experiment_name}
                        </h2>
                        <p className="mt-1 text-sm text-slate-300/80">
                          {entry.provider} / {entry.model} / {entry.workflow_kind}
                        </p>
                      </div>
                      <div className="rounded-2xl bg-emerald-500/15 px-4 py-3 text-right text-emerald-100 ring-1 ring-emerald-400/25">
                        <div className="text-xs uppercase tracking-[0.3em]">Score</div>
                        <div className="mt-1 text-2xl font-semibold">{formatScore(entry.aggregate_score)}</div>
                      </div>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-200/75">
                      <Pill>{entry.benchmark}</Pill>
                      {entry.tags.map((tag) => (
                        <Pill key={tag}>{tag}</Pill>
                      ))}
                    </div>
                  </article>
                ))
              )}
            </div>
          </Panel>

          <Panel title="Run Queue">
            <div className="space-y-3">
              {payload.runs.length === 0 ? (
                <EmptyState text="No runs recorded." />
              ) : (
                payload.runs.slice(0, 8).map((run) => (
                  <article
                    key={run.id}
                    className="rounded-3xl border border-white/8 bg-slate-950/35 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-white">{run.workflow_kind}</div>
                        <div className="text-xs text-slate-300/70">
                          Updated {formatDate(run.updated_at)}
                        </div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusTone(run.status)}`}>
                        {run.status}
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-3 text-sm text-slate-200/80">
                      <Metric label="Tasks" value={`${run.completed_task_count}/${run.total_task_count}`} />
                      <Metric label="Latency" value={`${run.latency_ms} ms`} />
                      <Metric label="Score" value={formatScore(run.aggregate_score)} />
                    </div>
                  </article>
                ))
              )}
            </div>
          </Panel>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-3">
          <Panel title="Experiment Registry">
            <div className="space-y-3">
              {payload.experiments.length === 0 ? (
                <EmptyState text="No experiments have been registered." />
              ) : (
                payload.experiments.slice(0, 8).map((experiment) => (
                  <article
                    key={experiment.id}
                    className="rounded-3xl border border-white/8 bg-slate-950/35 p-4"
                  >
                    <h3 className="text-base font-semibold text-white">{experiment.name}</h3>
                    <p className="mt-1 text-sm text-slate-300/75">
                      {experiment.provider} / {experiment.model}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300/70">
                      <Pill>{experiment.benchmark}</Pill>
                      {experiment.tags.map((tag) => (
                        <Pill key={tag}>{tag}</Pill>
                      ))}
                    </div>
                  </article>
                ))
              )}
            </div>
          </Panel>

          <Panel title="Synthetic Datasets">
            <div className="space-y-3">
              {payload.datasets.length === 0 ? (
                <EmptyState text="No synthetic datasets generated yet." />
              ) : (
                payload.datasets.slice(0, 8).map((dataset) => (
                  <article
                    key={dataset.id}
                    className="rounded-3xl border border-white/8 bg-slate-950/35 p-4"
                  >
                    <div className="text-sm font-medium text-white">{dataset.source_benchmark}</div>
                    <div className="mt-1 text-xs text-slate-300/70">
                      {dataset.provider} / {dataset.model}
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-200/80">
                      <Metric label="Generated" value={dataset.record_count.toString()} />
                      <Metric label="Deduped" value={dataset.deduped_record_count.toString()} />
                    </div>
                  </article>
                ))
              )}
            </div>
          </Panel>

          <Panel title="Submission Bundles">
            <div className="space-y-3">
              {payload.submissions.length === 0 ? (
                <EmptyState text="No submission bundles built yet." />
              ) : (
                payload.submissions.slice(0, 8).map((submission) => (
                  <article
                    key={submission.id}
                    className="rounded-3xl border border-white/8 bg-slate-950/35 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-sm font-medium text-white">
                          {submission.version} / {submission.status}
                        </div>
                        <div className="mt-1 text-xs text-slate-300/70">{submission.file_path}</div>
                      </div>
                      <span className="rounded-full bg-sky-500/12 px-3 py-1 text-xs text-sky-100 ring-1 ring-sky-400/25">
                        {submission.validation.valid ? "validated" : "review"}
                      </span>
                    </div>
                    {submission.validation.warnings[0] ? (
                      <p className="mt-3 text-xs leading-6 text-amber-100/85">
                        {submission.validation.warnings[0]}
                      </p>
                    ) : null}
                  </article>
                ))
              )}
            </div>
          </Panel>
        </section>
      </div>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/35 px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.25em] text-slate-300/65">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/6 p-5 shadow-[0_16px_60px_rgba(0,0,0,0.25)] backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight text-white">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/6 px-3 py-2">
      <div className="text-[11px] uppercase tracking-[0.25em] text-slate-300/65">{label}</div>
      <div className="mt-1 text-base font-medium text-white">{value}</div>
    </div>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1">{children}</span>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-white/12 bg-slate-950/20 p-6 text-sm text-slate-300/75">
      {text}
    </div>
  );
}

export default App;
