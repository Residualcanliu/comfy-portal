"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, API_URL, getToken } from "@/lib/api";
import type { WorkflowSummary } from "@comfy-portal/shared";

interface Artifact {
  id: number;
  kind: string;
  url: string;
  width: number;
  height: number;
}

export default function Create() {
  const { id } = useParams<{ id: string }>();
  const [wf, setWf] = useState<WorkflowSummary | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [taskId, setTaskId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<WorkflowSummary>(`/api/workflows/${id}`)
      .then((w) => {
        setWf(w);
        const init: Record<string, string> = {};
        for (const s of w.slots) {
          if (s.default !== undefined && s.default !== null) init[s.key] = String(s.default);
        }
        setValues(init);
      })
      .catch((e) => setErr((e as Error).message));
  }, [id]);

  useEffect(() => {
    if (taskId === null) return;
    const es = new EventSource(`${API_URL}/api/tasks/${taskId}/events`);
    es.addEventListener("status", (e) => {
      const d = JSON.parse((e as MessageEvent).data);
      setStatus(d.state);
    });
    es.addEventListener("progress", (e) => {
      const d = JSON.parse((e as MessageEvent).data);
      setProgress(d.pct);
    });
    es.addEventListener("done", (e) => {
      const d = JSON.parse((e as MessageEvent).data);
      setStatus("success");
      setProgress(100);
      setArtifacts(d.artifacts);
      es.close();
    });
    es.addEventListener("error", (e) => {
      const d = JSON.parse((e as MessageEvent).data);
      setStatus("failed");
      setErr(d.error);
      es.close();
    });
    es.onerror = () => es.close();
    return () => es.close();
  }, [taskId]);

  async function submit() {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    setErr("");
    setArtifacts([]);
    setProgress(null);
    try {
      const task = await api<{ id: number }>("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ workflow_id: Number(id), params: values }),
      });
      setTaskId(task.id);
      setStatus("queued");
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  if (wf === null) {
    return <p className="text-sm text-muted">{err || "加载中…"}</p>;
  }

  const inputCls =
    "mt-1 w-full rounded border border-line bg-surface px-3 py-2 text-sm text-fg placeholder:text-muted";

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <section>
        <h2 className="mb-4 text-xl font-semibold">{wf.name}</h2>
        <div className="space-y-4">
          {wf.slots.map((s) => (
            <label key={s.key} className="block">
              <span className="text-sm text-muted">
                {s.label}
                {s.required ? " *" : ""}
              </span>
              {s.type === "text" ? (
                <textarea
                  rows={3}
                  value={values[s.key] ?? ""}
                  onChange={(e) => setValues({ ...values, [s.key]: e.target.value })}
                  className={inputCls}
                />
              ) : (
                <input
                  type="number"
                  step={s.type === "float" ? "0.1" : "1"}
                  min={s.min}
                  max={s.max}
                  value={values[s.key] ?? ""}
                  onChange={(e) => setValues({ ...values, [s.key]: e.target.value })}
                  className={inputCls}
                />
              )}
            </label>
          ))}
          {err && <p className="text-sm text-red-400">{err}</p>}
          <button
            onClick={submit}
            disabled={status === "running" || status === "queued"}
            className="w-full rounded bg-fg py-2 font-medium text-bg disabled:opacity-50"
          >
            生成
          </button>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold">进度</h2>
        {status === "" ? (
          <p className="text-sm text-muted">尚未提交</p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm">状态：{status}</p>
            {progress !== null && (
              <div className="h-2 w-full rounded bg-surface-hover">
                <div
                  className="h-2 rounded bg-fg transition-all"
                  style={{ width: `${Math.min(progress, 100)}%` }}
                />
                <p className="mt-1 text-xs text-muted">{progress.toFixed(0)}%</p>
              </div>
            )}
            {artifacts.length > 0 && (
              <div className="grid grid-cols-1 gap-4">
                {artifacts.map((a) => (
                  <img
                    key={a.id}
                    src={`${API_URL}${a.url}`}
                    alt="生成结果"
                    className="rounded-lg border border-line"
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
