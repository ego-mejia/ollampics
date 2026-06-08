export type RunSummary = {
  id: number;
  created_at: string;
  status: string;
  config: {
    models: string[];
    suites: string[];
    notes?: string | null;
  };
  notes: string | null;
  n_attempts: number;
  n_successes: number;
};

export type RunStatus = {
  id: number;
  status: string;
  n_attempts: number;
  n_successes: number;
};

export type AttemptSummary = {
  id: number;
  model: string;
  task_id: string;
  try_n: number;
  status: string;
  tps_decode: number | null;
  ttft_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  peak_vram_mb: number | null;
  avg_watts: number | null;
  wall_time_s: number | null;
};

export type RunDetail = RunSummary & { attempts: AttemptSummary[] };

export type ModelInfo = {
  name: string;
  size_bytes: number;
  modified_at: string | null;
};

export type SuiteMeta = {
  name: string;
  tasks: { task_id: string; version: number; description: string; max_tries: number }[];
};

export type LeaderboardEntry = {
  model: string;
  runtime_hash: string;
  suite: string;
  n_tasks: number;
  successes: number;
  success_rate: number;
  avg_tps: number | null;
  avg_ttft_ms: number | null;
  avg_tries: number;
  peak_vram_mb: number | null;
};

export type RuntimeConfig = {
  num_ctx: number;
  kv_cache_type: string;
  temperature: number;
  seed: number;
  top_p: number;
};

export type RunConfigPayload = {
  models: string[];
  runtime_configs: RuntimeConfig[];
  suites: string[];
  notes: string | null;
};

const BASE = "/api";

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

export const fetchRuns = () => getJson<RunSummary[]>(`/runs`);
export const fetchRun = (id: number) => getJson<RunDetail>(`/runs/${id}`);
export const fetchRunStatus = (id: number) => getJson<RunStatus>(`/runs/${id}/status`);
export const fetchModels = () => getJson<ModelInfo[]>(`/models`);
export const fetchSuites = () => getJson<SuiteMeta[]>(`/suites`);
export const fetchLeaderboard = (suite?: string, metric = "success_rate") => {
  const params = new URLSearchParams({ metric });
  if (suite) params.set("suite", suite);
  return getJson<LeaderboardEntry[]>(`/leaderboard?${params}`);
};

export async function deleteRun(id: number): Promise<void> {
  const r = await fetch(`${BASE}/runs/${id}`, { method: "DELETE" });
  if (!r.ok && r.status !== 204) {
    throw new Error(`deleteRun: ${r.status} ${await r.text()}`);
  }
}

export async function createRun(payload: RunConfigPayload): Promise<RunSummary> {
  const r = await fetch(`${BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`createRun: ${r.status} ${await r.text()}`);
  return r.json();
}

// — Tests page —

export type SuiteCard = {
  name: string;
  label: string;
  description: string;
  icon: string;
  n_tasks: number;
  has_corpus: boolean;
};

export type SuiteDetail = {
  name: string;
  label: string;
  description: string;
  icon: string;
  n_tasks: number;
  tasks: { task_id: string; version: number; description: string; max_tries: number }[];
};

export type CorpusDoc = {
  name: string;
  size_bytes: number;
  n_lines: number;
  preview: string;
  content: string | null;
};

export type PromptFile = {
  name: string;
  size_bytes: number;
  content: string;
};

export const fetchTests = () => getJson<SuiteCard[]>(`/tests`);
export const fetchTestDetail = (suite: string) => getJson<SuiteDetail>(`/tests/${suite}`);
export const fetchCorpusDocs = () => getJson<CorpusDoc[]>(`/corpus/rag`);
export const fetchCorpusDoc = (name: string) =>
  getJson<CorpusDoc>(`/corpus/rag/${encodeURIComponent(name)}`);
export const fetchCorpusPrompts = () => getJson<PromptFile[]>(`/corpus/prompts`);

export async function triggerCorpusGenerate(
  overwrite = false
): Promise<{ status: string; started_at: string }> {
  const r = await fetch(`${BASE}/corpus/generate?overwrite=${overwrite}`, {
    method: "POST",
  });
  if (!r.ok) throw new Error(`generate: ${r.status} ${await r.text()}`);
  return r.json();
}

// — Compare —

export type RunBrief = {
  id: number;
  created_at: string;
  status: string;
  model: string | null;
  runtime_hash: string | null;
  num_ctx: number | null;
  kv_cache_type: string | null;
  notes: string | null;
  n_tasks: number;
  n_successes: number;
};

export type CompareEntry = {
  task_id: string;
  suite: string;
  a_status: string | null;
  a_tps: number | null;
  a_ttft_ms: number | null;
  a_tokens_out: number | null;
  a_wall_s: number | null;
  b_status: string | null;
  b_tps: number | null;
  b_ttft_ms: number | null;
  b_tokens_out: number | null;
  b_wall_s: number | null;
};

export type CompareResponse = {
  run_a: RunBrief;
  run_b: RunBrief;
  entries: CompareEntry[];
  summary: {
    a_only_success: number;
    b_only_success: number;
    both_success: number;
    n_shared_tasks: number;
  };
};

export const fetchCompareOptions = () => getJson<RunBrief[]>(`/compare/options`);
export const fetchCompare = (a: number, b: number) =>
  getJson<CompareResponse>(`/compare?a=${a}&b=${b}`);

// — WebSocket for live run events —

export type RunEvent = {
  event: string;
  payload: Record<string, unknown>;
};

export function openRunWebSocket(
  runId: number,
  onEvent: (e: RunEvent) => void,
  onClose?: () => void
): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const url = `${proto}//${host}/api/runs/${runId}/ws`;
  const ws = new WebSocket(url);
  ws.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data));
    } catch (_e) {
      // ignore malformed
    }
  };
  ws.onclose = () => {
    onClose?.();
  };
  return ws;
}
