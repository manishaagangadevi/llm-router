"use client";

import { useState, useRef, useEffect } from "react";
import TopNav from "@/components/TopNav";
import { sendQuery, sendFeedback, QueryResponse } from "@/lib/api";

type Priority = "balanced" | "cost" | "quality";

interface Message {
  role: "user" | "assistant";
  text: string;
  meta?: QueryResponse;
  detailsOpen?: boolean;
  feedbackGiven?: 1 | -1;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [priority, setPriority] = useState<Priority>("balanced");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const query = input.trim();
    if (!query || loading) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setLoading(true);

    try {
      const res = await sendQuery(query, priority);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer, meta: res }]);
    } catch {
      setError("Couldn't reach the router backend. Is it running on localhost:8000?");
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(index: number, logId: number, value: 1 | -1) {
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, feedbackGiven: value } : m)));
    try {
      await sendFeedback(logId, value);
    } catch {
      // non-critical: the rating just isn't recorded
    }
  }

  function toggleDetails(index: number) {
    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, detailsOpen: !m.detailsOpen } : m))
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <TopNav />

      <main className="flex-1 flex flex-col mx-auto w-full max-w-3xl px-6">
        <div className="flex-1 overflow-y-auto py-8 space-y-6">
          {messages.length === 0 && (
            <div className="pt-24 text-center">
              <p className="text-text-primary text-lg">Ask anything.</p>
              <p className="text-text-secondary text-sm mt-1">
                Every query is compressed and routed to the right model automatically.
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={m.role === "user" ? "max-w-[80%]" : "max-w-[85%] w-full"}>
                <div
                  className={
                    m.role === "user"
                      ? "bg-bg-2 border border-border rounded-2xl px-4 py-2.5 text-sm"
                      : "text-sm text-text-primary leading-relaxed whitespace-pre-wrap"
                  }
                >
                  {m.text}
                </div>

                {m.role === "assistant" && m.meta && (
                  <div className="mt-2">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleDetails(i)}
                        className="text-xs text-text-muted hover:text-teal transition-colors font-mono"
                      >
                        {m.detailsOpen ? "− hide routing details" : "+ routing details"}
                      </button>
                      <button
                        onClick={() => handleFeedback(i, m.meta!.log_id, 1)}
                        aria-label="Good response"
                        className={`text-xs transition-colors ${
                          m.feedbackGiven === 1 ? "text-teal" : "text-text-muted hover:text-teal"
                        }`}
                      >
                        ▲
                      </button>
                      <button
                        onClick={() => handleFeedback(i, m.meta!.log_id, -1)}
                        aria-label="Bad response"
                        className={`text-xs transition-colors ${
                          m.feedbackGiven === -1 ? "text-amber" : "text-text-muted hover:text-amber"
                        }`}
                      >
                        ▼
                      </button>
                    </div>

                    {m.detailsOpen && (
                      <div className="mt-2 border border-border rounded-lg px-4 py-3 bg-bg-1 grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2 text-xs font-mono">
                        <Detail label="model" value={m.meta.model_used} accent />
                        <Detail
                          label="cache"
                          value={m.meta.cache_hit ? "hit" : "miss"}
                          accent={m.meta.cache_hit}
                        />
                        <Detail label="latency" value={`${m.meta.latency_ms}ms`} />
                        <Detail
                          label="tokens"
                          value={`${m.meta.original_tokens} → ${m.meta.compressed_tokens} (−${m.meta.tokens_saved_pct}%)`}
                        />
                        <Detail label="cost" value={`$${m.meta.estimated_cost_usd.toFixed(6)}`} />
                        <Detail label="reason" value={m.meta.routing_reason} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-text-muted text-sm font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-teal animate-pulse" />
              routing…
            </div>
          )}

          {error && <p className="text-sm text-amber">{error}</p>}
          <div ref={bottomRef} />
        </div>

        <div className="sticky bottom-0 pb-6 pt-3 bg-bg-0">
          <div className="border border-border-strong rounded-2xl bg-bg-1 px-4 py-3 focus-within:border-teal/50 transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything…"
              rows={1}
              className="w-full bg-transparent resize-none outline-none text-sm text-text-primary placeholder:text-text-muted"
            />
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-1">
                {(["cost", "balanced", "quality"] as Priority[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPriority(p)}
                    className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                      priority === p
                        ? "border-teal/40 text-teal bg-teal-dim"
                        : "border-border text-text-muted hover:text-text-secondary"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="text-xs font-medium px-3.5 py-1.5 rounded-full bg-teal text-bg-0 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Detail({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <span className="text-text-muted">{label} </span>
      <span className={accent ? "text-teal" : "text-text-secondary"}>{value}</span>
    </div>
  );
}
