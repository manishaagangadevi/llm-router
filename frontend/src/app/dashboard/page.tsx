"use client";

import { useEffect, useState } from "react";
import TopNav from "@/components/TopNav";
import { getStats, getLogs, Stats, LogEntry } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, l] = await Promise.all([getStats(), getLogs()]);
        setStats(s);
        setLogs(l);
      } catch {
        setError(true);
      }
    };
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = stats
    ? Object.entries(stats.model_distribution).map(([model, count]) => ({
        model: model.replace("claude-", ""),
        count,
      }))
    : [];

  return (
    <div className="flex flex-col min-h-screen">
      <TopNav />
      <main className="flex-1 mx-auto w-full max-w-5xl px-6 py-10">
        {error && (
          <p className="text-sm text-amber mb-6">
            Couldn&apos;t reach the router backend. Is it running on localhost:8000?
          </p>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <HeroStat
            label="cost saved"
            value={stats ? `$${stats.estimated_cost_saved_usd.toFixed(4)}` : "—"}
            hero
          />
          <Stat label="total requests" value={stats ? String(stats.total_requests) : "—"} />
          <Stat label="cache hit rate" value={stats ? `${stats.cache_hit_rate_pct}%` : "—"} />
          <Stat label="avg tokens saved" value={stats ? `${stats.avg_tokens_saved_pct}%` : "—"} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-border rounded-xl bg-bg-1 p-5">
            <p className="text-xs font-mono text-text-muted mb-4">model distribution</p>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="model"
                    tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
                    axisLine={{ stroke: "var(--border)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-2)",
                      border: "1px solid var(--border-strong)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="var(--teal)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-text-muted text-sm h-[200px] flex items-center justify-center">
                No requests yet
              </p>
            )}
          </div>

          <div className="border border-border rounded-xl bg-bg-1 p-5">
            <p className="text-xs font-mono text-text-muted mb-4">recent requests</p>
            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
              {logs.length === 0 && <p className="text-text-muted text-sm">No requests yet</p>}
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between text-xs font-mono py-1.5 border-b border-border last:border-0"
                >
                  <span className="text-text-secondary truncate max-w-[140px]">
                    {log.query_preview}
                  </span>
                  <span className={log.cache_hit ? "text-teal" : "text-text-muted"}>
                    {log.model_used.replace("claude-", "")}
                  </span>
                  <span className="text-text-muted">{log.latency_ms}ms</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-border rounded-xl bg-bg-1 p-4">
      <p className="text-xs text-text-muted mb-1.5">{label}</p>
      <p className="text-xl font-mono text-text-primary">{value}</p>
    </div>
  );
}

function HeroStat({ label, value }: { label: string; value: string; hero?: boolean }) {
  return (
    <div className="col-span-2 border border-amber/25 rounded-xl bg-amber-dim p-4">
      <p className="text-xs text-amber/80 mb-1.5">{label}</p>
      <p className="text-3xl font-mono text-amber">{value}</p>
    </div>
  );
}
