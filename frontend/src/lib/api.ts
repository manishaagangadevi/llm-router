const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface QueryResponse {
  log_id: number;
  answer: string;
  model_used: string;
  original_tokens: number;
  compressed_tokens: number;
  tokens_saved_pct: number;
  cache_hit: boolean;
  latency_ms: number;
  estimated_cost_usd: number;
  routing_reason: string;
}

export interface LogEntry {
  id: number;
  query_preview: string;
  model_used: string;
  tokens_saved_pct: number;
  latency_ms: number;
  estimated_cost_usd: number;
  cache_hit: boolean;
  created_at: string;
}

export interface Stats {
  total_requests: number;
  cache_hit_rate_pct: number;
  total_cost_usd: number;
  estimated_cost_saved_usd: number;
  avg_tokens_saved_pct: number;
  model_distribution: Record<string, number>;
  generated_at: string;
}

export async function sendQuery(query: string, priority: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, priority }),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function sendFeedback(logId: number, feedback: 1 | -1): Promise<void> {
  await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ log_id: logId, feedback }),
  });
}

export async function getLogs(): Promise<LogEntry[]> {
  const res = await fetch(`${API_BASE}/api/logs`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}
