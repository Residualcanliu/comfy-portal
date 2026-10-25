"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";
import Spinner from "@/components/Spinner";
import type { WorkflowSummary } from "@comfy-portal/shared";

interface GalleryItem {
  id: number;
  url: string;
  width: number;
  height: number;
}

interface Stats {
  totals: {
    tasks: number;
    success: number;
    failed: number;
    cancelled: number;
    artifacts: number;
  };
  success_rate: number | null;
  avg_duration_seconds: number | null;
}

export default function Home() {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [gallery, setGallery] = useState<GalleryItem[]>([]);
  const [queueLength, setQueueLength] = useState<number | null>(null);
  const [gpuOnline, setGpuOnline] = useState<boolean | null>(null);
  const [readonlyDemo, setReadonlyDemo] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [workflowsLoading, setWorkflowsLoading] = useState(true);
  const [galleryLoading, setGalleryLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    api<WorkflowSummary[]>("/api/workflows?official=1")
      .then(setWorkflows)
      .catch(console.error)
      .finally(() => setWorkflowsLoading(false));
    api<GalleryItem[]>("/api/gallery")
      .then(setGallery)
      .catch(console.error)
      .finally(() => setGalleryLoading(false));
    api<{ queue_length: number; gpu_online: boolean; readonly_demo: boolean }>("/api/status")
      .then((s) => {
        setQueueLength(s.queue_length);
        setGpuOnline(s.gpu_online);
        setReadonlyDemo(s.readonly_demo);
      })
      .catch(console.error);
    api<Stats>("/api/stats")
      .then(setStats)
      .catch(console.error);
    api<{ is_admin: boolean }>("/api/auth/me")
      .then((m) => setIsAdmin(m.is_admin))
      .catch(() => {});
  }, []);

  async function deleteArtifact(id: number) {
    if (!confirm("确定删除这张作品吗？")) return;
    try {
      await api(`/api/gallery/${id}`, { method: "DELETE" });
      setGallery((g) => g.filter((x) => x.id !== id));
    } catch (e) {
      alert((e as Error).message);
    }
  }

  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="animate-fade-up py-10">
        <h1 className="text-4xl font-black leading-tight tracking-tight md:text-6xl">
          用 AI 生成
          <br />
          <span className="bg-gradient-to-r from-violet-500 via-purple-500 to-blue-500 bg-clip-text text-transparent">
            你的下一张图
          </span>
        </h1>
        <p className="mt-4 text-lg font-semibold text-amber-400">
          维修中，暂不开启功能
        </p>
        <p className="mt-3 max-w-xl text-lg text-muted">
          选工作流 → 填提示词 → 几秒出图，实时看到进度
        </p>
        {readonlyDemo ? (
          <>
            <p className="mt-5 max-w-2xl rounded-xl border border-line bg-surface px-4 py-3 text-sm leading-relaxed text-muted">
              本项目为个人技术研究与学习项目，仅用于展示系统架构与工程实践。
              公开站点为只读演示，不提供生成式人工智能服务。
            </p>
            <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-muted">
              <span className="h-2 w-2 rounded-full bg-zinc-400" />
              <span>只读演示站 · 已关闭生成</span>
            </div>
          </>
        ) : (
          gpuOnline !== null && (
            <div
              className={`mt-5 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${
                gpuOnline
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${gpuOnline ? "bg-emerald-400" : "bg-amber-400"}`}
              />
              <span>{gpuOnline ? "主机在线 · 可立即生成" : "主机离线 · 可提交，稍后生成"}</span>
            </div>
          )
        )}
        <div className="mt-8 flex gap-3">
          <a
            href="#workflows"
            className="rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-6 py-3 font-semibold text-white transition hover:opacity-90"
          >
            {readonlyDemo ? "浏览工作流" : "开始生成"}
          </a>
          <a
            href="#gallery"
            className="rounded-full border border-line px-6 py-3 font-semibold transition hover:border-muted"
          >
            浏览画廊
          </a>
        </div>
      </section>

      {/* 数据条 */}
      <section className="animate-fade-up grid grid-cols-3 gap-4 border-y border-line py-8">
        {[
          { n: workflows.length, label: "预置工作流" },
          { n: queueLength ?? "—", label: "当前排队数" },
          { n: gallery.length, label: "生成作品" },
        ].map((s) => (
          <div key={s.label} className="text-center">
            <div className="text-3xl font-black md:text-4xl">{s.n}</div>
            <div className="mt-1 text-sm text-muted">{s.label}</div>
          </div>
        ))}
      </section>

      {/* 工作流 */}
      <section id="workflows" className="animate-fade-up scroll-mt-20">
        <h2 className="mb-5 text-sm font-semibold uppercase tracking-wider text-muted">
          工作流 · 选一个开始
        </h2>
        {workflowsLoading ? (
          <div className="flex items-center gap-3 py-10 text-accent">
            <Spinner className="h-5 w-5" />
            <span className="text-sm text-muted">正在加载工作流…</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {workflows.map((w) => (
              <a
                key={w.id}
                href={`/create/${w.id}`}
                className="group card-shine rounded-xl border border-line bg-surface p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent"
              >
                <div className="font-bold">{w.name}</div>
                <div className="mt-1 text-xs text-muted">{w.description}</div>
                <div className="mt-3 text-sm font-semibold text-accent opacity-0 transition group-hover:opacity-100">
                  {readonlyDemo ? "查看参数 →" : "开始生成 →"}
                </div>
              </a>
            ))}
          </div>
        )}
      </section>

      {/* 技术展示 */}
      <section id="tech" className="animate-fade-up scroll-mt-20">
        <div className="mb-5 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
            系统与架构
          </h2>
          <a
            href="https://github.com/Residualcanliu/comfy-portal"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-accent hover:underline"
          >
            查看源码 ↗
          </a>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { n: stats?.totals.tasks ?? "—", label: "累计任务" },
            {
              n:
                stats?.success_rate != null
                  ? `${Math.round(stats.success_rate * 100)}%`
                  : "—",
              label: "成功率",
            },
            { n: stats?.totals.artifacts ?? "—", label: "生成作品" },
            {
              n:
                stats?.avg_duration_seconds != null
                  ? `${stats.avg_duration_seconds}s`
                  : "—",
              label: "平均出图",
            },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-xl border border-line bg-surface p-4 text-center"
            >
              <div className="text-2xl font-black">{s.n}</div>
              <div className="mt-1 text-xs text-muted">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-xl border border-line bg-surface p-5">
          <h3 className="font-bold">控制面 / 计算面分离</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            云端 VPS 只跑控制面，负责认证、排队、状态与推送；本地 GPU
            节点通过 Tailscale 接入，只执行生成任务。GPU
            关机时任务照常入队，开机后自动续跑。
          </p>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-5">
            {[
              "浏览器",
              "Vercel 前端",
              "FastAPI 控制面",
              "Redis + RQ",
              "本地 GPU + ComfyUI",
            ].map((item, i) => (
              <div key={item} className="flex items-center gap-2">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-xs font-bold text-violet-400">
                  {i + 1}
                </span>
                <span className="text-muted">{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            {
              title: "异步队列 + SSE",
              body: "任务经 Redis + RQ 排队，worker 把 ComfyUI 的采样进度发布到 Redis，API 通过 SSE 实时推给浏览器。",
            },
            {
              title: "三层故障恢复",
              body: "30 秒心跳判定节点在线、last_activity 检测卡死任务、后台线程对账 RQ 注册表回收孤儿任务。",
            },
            {
              title: "零公网暴露的 GPU",
              body: "ComfyUI 只监听本地回环，控制面与 GPU 通过 Tailscale 组网，内部接口再叠加 token 与源 IP 双闸门。",
            },
          ].map((x) => (
            <div
              key={x.title}
              className="card-shine rounded-xl border border-line bg-surface p-4"
            >
              <h3 className="font-bold">{x.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{x.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-line bg-surface p-5">
            <h3 className="font-bold">技术栈</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                "FastAPI",
                "PostgreSQL",
                "Redis",
                "RQ",
                "SSE",
                "Tailscale",
                "Prometheus",
                "Grafana",
                "Next.js",
                "Docker",
              ].map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-line px-2.5 py-1 text-xs text-muted"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-line bg-surface p-5">
            <h3 className="font-bold">实测出图耗时</h3>
            <div className="mt-3 space-y-2 text-sm">
              {[
                { model: "SD1.5", cold: "20.1s", warm: "5.8s" },
                { model: "SDXL", cold: "49.5s", warm: "7.1s" },
                { model: "FLUX.1-dev", cold: "98.7s", warm: "38.2s" },
              ].map((row) => (
                <div
                  key={row.model}
                  className="flex items-center justify-between gap-3"
                >
                  <span className="text-muted">{row.model}</span>
                  <span className="text-xs text-muted">
                    冷启动 {row.cold} · 热态 {row.warm}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 画廊 */}
      <section id="gallery" className="animate-fade-up scroll-mt-20">
        <div className="mb-5 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">画廊</h2>
          <span className="text-sm text-muted">{gallery.length} 张作品</span>
        </div>
        {galleryLoading ? (
          <div className="flex items-center gap-3 py-10 text-accent">
            <Spinner className="h-5 w-5" />
            <span className="text-sm text-muted">正在加载画廊…</span>
          </div>
        ) : gallery.length === 0 ? (
          <p className="text-sm text-muted">暂无作品，去上面选个工作流生成第一张图吧</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {gallery.map((g) => (
              <div
                key={g.id}
                className="group relative aspect-square overflow-hidden rounded-lg border border-line"
              >
                <a
                  href={`${API_URL}${g.url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="block h-full w-full"
                >
                  <img
                    src={`${API_URL}${g.url}`}
                    alt={`作品 ${g.id}`}
                    className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                  />
                  <div className="pointer-events-none absolute inset-0 flex items-end bg-gradient-to-t from-black/60 via-transparent to-transparent p-3 opacity-0 transition duration-300 group-hover:opacity-100">
                    <span className="text-xs text-white">
                      {g.width} × {g.height}
                    </span>
                  </div>
                </a>
                {isAdmin && (
                  <button
                    onClick={() => deleteArtifact(g.id)}
                    className="absolute right-2 top-2 rounded-full bg-red-500/80 px-2.5 py-1 text-xs text-white opacity-0 transition group-hover:opacity-100 hover:bg-red-600"
                  >
                    删除
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 结尾 CTA */}
      <section className="animate-fade-up rounded-2xl border border-line bg-surface p-10 text-center">
        <h2 className="text-3xl font-black tracking-tight">
          {readonlyDemo ? "这是一个只读演示站" : "准备好生成你的第一张图了吗？"}
        </h2>
        <p className="mt-2 text-muted">
          {readonlyDemo
            ? "生成能力因合规原因关闭，架构、源码与实测数据全部公开。"
            : "免费注册，选个工作流，几秒出图"}
        </p>
        {readonlyDemo ? (
          <a
            href="https://github.com/Residualcanliu/comfy-portal"
            target="_blank"
            rel="noreferrer"
            className="mt-6 inline-block rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-8 py-3 font-semibold text-white transition hover:opacity-90"
          >
            查看源码 ↗
          </a>
        ) : (
          <a
            href="#workflows"
            className="mt-6 inline-block rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-8 py-3 font-semibold text-white transition hover:opacity-90"
          >
            开始生成
          </a>
        )}
      </section>
    </div>
  );
}
