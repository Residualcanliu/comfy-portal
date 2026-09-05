"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";
import type { WorkflowSummary } from "@comfy-portal/shared";

interface GalleryItem {
  id: number;
  url: string;
  width: number;
  height: number;
}

export default function Home() {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [gallery, setGallery] = useState<GalleryItem[]>([]);
  const [queueLength, setQueueLength] = useState<number | null>(null);

  useEffect(() => {
    api<WorkflowSummary[]>("/api/workflows?official=1")
      .then(setWorkflows)
      .catch(console.error);
    api<GalleryItem[]>("/api/gallery").then(setGallery).catch(console.error);
    api<{ queue_length: number }>("/api/status")
      .then((s) => setQueueLength(s.queue_length))
      .catch(console.error);
  }, []);

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
        <p className="mt-4 max-w-xl text-lg text-muted">
          选工作流 → 填提示词 → 几秒出图，实时看到进度
        </p>
        <div className="mt-8 flex gap-3">
          <a
            href="#workflows"
            className="rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-6 py-3 font-semibold text-white transition hover:opacity-90"
          >
            开始生成
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
                开始生成 →
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* 画廊 */}
      <section id="gallery" className="animate-fade-up scroll-mt-20">
        <div className="mb-5 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">画廊</h2>
          <span className="text-sm text-muted">{gallery.length} 张作品</span>
        </div>
        {gallery.length === 0 ? (
          <p className="text-sm text-muted">暂无作品，去上面选个工作流生成第一张图吧</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {gallery.map((g) => (
              <a
                key={g.id}
                href={`${API_URL}${g.url}`}
                target="_blank"
                rel="noreferrer"
                className="group relative aspect-square overflow-hidden rounded-lg border border-line"
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
            ))}
          </div>
        )}
      </section>

      {/* 结尾 CTA */}
      <section className="animate-fade-up rounded-2xl border border-line bg-surface p-10 text-center">
        <h2 className="text-3xl font-black tracking-tight">准备好生成你的第一张图了吗？</h2>
        <p className="mt-2 text-muted">免费注册，选个工作流，几秒出图</p>
        <a
          href="#workflows"
          className="mt-6 inline-block rounded-full bg-gradient-to-r from-violet-500 to-blue-500 px-8 py-3 font-semibold text-white transition hover:opacity-90"
        >
          开始生成
        </a>
      </section>
    </div>
  );
}
