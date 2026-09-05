"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, API_URL, getToken } from "@/lib/api";
import Spinner from "@/components/Spinner";
import type { WorkflowSummary } from "@comfy-portal/shared";

interface Artifact {
  id: number;
  kind: string;
  url: string;
  width: number;
  height: number;
}

// 任务状态 → 中文 + 配色
const STATUS_META: Record<string, { label: string; cls: string }> = {
  queued: { label: "排队中", cls: "bg-amber-500/15 text-amber-400" },
  running: { label: "生成中", cls: "bg-blue-500/15 text-blue-400" },
  processing: { label: "生成中", cls: "bg-blue-500/15 text-blue-400" },
  success: { label: "已完成", cls: "bg-emerald-500/15 text-emerald-400" },
  completed: { label: "已完成", cls: "bg-emerald-500/15 text-emerald-400" },
  failed: { label: "失败", cls: "bg-red-500/15 text-red-400" },
  error: { label: "失败", cls: "bg-red-500/15 text-red-400" },
  cancelled: { label: "已取消", cls: "bg-zinc-500/15 text-zinc-400" },
};

// 预设风格（英文提示词，提交时追加到 prompt 末尾）
const STYLES: { key: string; label: string; prompt: string }[] = [
  { key: "photo", label: "写实摄影", prompt: "photorealistic, 8k, sharp focus, natural lighting, shot on DSLR, 85mm lens" },
  { key: "cyberpunk", label: "赛博朋克", prompt: "cyberpunk style, neon lights, futuristic city, holographic, high contrast" },
  { key: "ink", label: "水墨国风", prompt: "traditional chinese ink wash painting, watercolor, elegant brush strokes, minimalist" },
  { key: "anime", label: "动漫", prompt: "anime style, clean lineart, cel shading, vibrant colors, studio ghibli aesthetic" },
  { key: "cinematic", label: "电影感", prompt: "cinematic lighting, film grain, dramatic shadows, anamorphic lens, moody atmosphere" },
  { key: "oil", label: "油画", prompt: "oil painting, impasto texture, classical art, chiaroscuro, masterpiece" },
  { key: "3d", label: "3D 渲染", prompt: "3d render, octane, blender, ray tracing, subsurface scattering, highly detailed" },
  { key: "minimal", label: "极简", prompt: "minimalist, clean, flat design, lots of negative space" },
];

type PresetKey = "fast" | "balanced" | "quality";

export default function Create() {
  const { id } = useParams<{ id: string }>();
  const [wf, setWf] = useState<WorkflowSummary | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [defaultSteps, setDefaultSteps] = useState(30);
  const [preset, setPreset] = useState<PresetKey>("balanced");
  const [styleKey, setStyleKey] = useState<string>("");
  const [customStyle, setCustomStyle] = useState<string>("");
  const [taskId, setTaskId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [queueLength, setQueueLength] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<WorkflowSummary>(`/api/workflows/${id}`)
      .then((w) => {
        setWf(w);
        const init: Record<string, string> = {};
        let steps = 30;
        for (const s of w.slots) {
          if (s.default !== undefined && s.default !== null) init[s.key] = String(s.default);
          if (s.key === "steps") steps = Number(s.default ?? 30);
        }
        setDefaultSteps(steps);
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

  // 排队时轮询队列长度（显示「前方 N 人」）
  useEffect(() => {
    if (taskId === null || status !== "queued") return;
    const poll = () =>
      api<{ queue_length: number }>("/api/status")
        .then((s) => setQueueLength(s.queue_length))
        .catch(() => {});
    poll();
    const t = setInterval(poll, 3000);
    return () => clearInterval(t);
  }, [taskId, status]);

  // 画质预设：快速 ≈ 0.6×steps，均衡 = 默认，精细 ≈ 1.4×steps
  const presets: Record<PresetKey, { label: string; hint: string; steps: number }> = {
    fast: { label: "快速", hint: "更快", steps: Math.max(15, Math.round(defaultSteps * 0.6)) },
    balanced: { label: "均衡", hint: "推荐", steps: defaultSteps },
    quality: { label: "精细", hint: "更慢更细", steps: Math.min(150, Math.round(defaultSteps * 1.4)) },
  };

  function applyPreset(key: PresetKey) {
    setPreset(key);
    setValues((v) => ({ ...v, steps: String(presets[key].steps) }));
  }

  async function downloadImage(url: string, id: number) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      // 按真实文件后缀命名（图可能是 jpg/png）
      const ext = (url.split(".").pop() ?? "png").split("?")[0];
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `comfyportal-${id}.${ext}`;
      a.style.display = "none";
      document.body.appendChild(a);
      a.click();
      a.remove();
      // 延迟释放，避免浏览器还没读完 blob 就被 revoke
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 2000);
    } catch {
      // fetch 失败兜底：新标签打开原图，用户可右键保存
      window.open(url, "_blank", "noopener");
    }
  }

  async function submit() {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    setErr("");
    setArtifacts([]);
    setProgress(null);
    setQueueLength(null);
    // 风格词（预设或自定义）拼到 prompt 末尾
    const stylePrompt =
      styleKey === "custom"
        ? customStyle.trim()
        : (STYLES.find((s) => s.key === styleKey)?.prompt ?? "");
    const basePrompt = (values["prompt"] ?? "").trim();
    const params = { ...values, prompt: basePrompt + (stylePrompt ? `, ${stylePrompt}` : "") };
    try {
      const task = await api<{ id: number }>("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ workflow_id: Number(id), params }),
      });
      setTaskId(task.id);
      setStatus("queued");
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  if (wf === null) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
        {err ? (
          <>
            <p className="text-sm text-red-400">加载失败：{err}</p>
            <button
              onClick={() => window.location.reload()}
              className="rounded-full border border-line px-4 py-1.5 text-sm transition hover:border-muted"
            >
              重试
            </button>
          </>
        ) : (
          <>
            <Spinner className="h-8 w-8 text-accent" />
            <p className="text-sm text-muted">正在加载工作流…</p>
          </>
        )}
      </div>
    );
  }

  const inputCls =
    "mt-1 w-full rounded border border-line bg-surface px-3 py-2 text-sm text-fg placeholder:text-muted";
  const meta = STATUS_META[status] ?? { label: status || "待提交", cls: "bg-zinc-500/15 text-zinc-400" };
  const chip = (key: string) =>
    `rounded-full border px-3 py-1 text-sm transition ${
      styleKey === key
        ? "border-accent bg-accent/10 text-fg"
        : "border-line bg-surface text-muted hover:border-muted"
    }`;

  return (
    <div>
      <Link
        href="/"
        className="mb-5 inline-flex items-center gap-1.5 text-sm text-muted transition hover:text-fg"
      >
        ← 返回主页
      </Link>

      <div className="grid gap-8 md:grid-cols-2">
        {/* 左：参数表单 */}
        <section>
          <h2 className="mb-4 text-xl font-semibold">{wf.name}</h2>

          {/* 画质预设 */}
          <div className="mb-4">
            <div className="mb-1.5 text-sm text-muted">画质</div>
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(presets) as PresetKey[]).map((k) => (
                <button
                  key={k}
                  onClick={() => applyPreset(k)}
                  className={`rounded-lg border px-2 py-2 text-center transition ${
                    preset === k
                      ? "border-accent bg-accent/10 text-fg"
                      : "border-line bg-surface text-muted hover:border-muted"
                  }`}
                >
                  <div className="text-sm font-semibold">{presets[k].label}</div>
                  <div className="mt-0.5 text-xs opacity-70">{presets[k].hint}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 风格选择 */}
          <div className="mb-4">
            <div className="mb-1.5 text-sm text-muted">风格（可选）</div>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setStyleKey("")} className={chip("")}>
                无
              </button>
              {STYLES.map((s) => (
                <button key={s.key} onClick={() => setStyleKey(s.key)} className={chip(s.key)}>
                  {s.label}
                </button>
              ))}
              <button onClick={() => setStyleKey("custom")} className={chip("custom")}>
                自定义
              </button>
            </div>
            {styleKey === "custom" && (
              <input
                value={customStyle}
                onChange={(e) => setCustomStyle(e.target.value)}
                placeholder="输入自定义风格词，如：steampunk, watercolor, fantasy art…"
                className={inputCls}
              />
            )}
          </div>

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
              disabled={status === "running" || status === "queued" || status === "processing"}
              className="w-full rounded bg-gradient-to-r from-violet-500 to-blue-500 py-2 font-medium text-white transition hover:opacity-90 disabled:opacity-50"
            >
              生成
            </button>
          </div>
        </section>

        {/* 右：进度 + 结果 */}
        <section>
          <h2 className="mb-4 text-xl font-semibold">进度</h2>
          {status === "" ? (
            <p className="text-sm text-muted">尚未提交</p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${meta.cls}`}>
                  {meta.label}
                </span>
                {(status === "queued" || status === "running" || status === "processing") && (
                  <Spinner className="h-4 w-4 text-accent" />
                )}
                {status === "queued" && queueLength !== null && (
                  <span className="text-sm text-muted">前方 {queueLength} 人</span>
                )}
              </div>

              {progress !== null && (
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span className="text-muted">生成进度</span>
                    <span className="font-mono text-fg">{Math.min(progress, 100).toFixed(0)}%</span>
                  </div>
                  <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-surface-hover">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-violet-500 via-purple-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                    <div className="bar-shimmer" />
                  </div>
                </div>
              )}

              {artifacts.length > 0 && (
                <div className="space-y-3">
                  {artifacts.map((a) => (
                    <div
                      key={a.id}
                      className="overflow-hidden rounded-xl border border-line bg-surface/60 p-2"
                    >
                      <img
                        src={`${API_URL}${a.url}`}
                        alt={`生成结果 ${a.id}`}
                        className="mx-auto max-h-[420px] w-auto rounded-lg object-contain"
                      />
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={() => downloadImage(`${API_URL}${a.url}`, a.id)}
                          className="rounded-full border border-line px-3 py-1 text-xs transition hover:border-accent hover:text-accent"
                        >
                          下载图片
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
