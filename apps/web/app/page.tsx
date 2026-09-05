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

  useEffect(() => {
    api<WorkflowSummary[]>("/api/workflows?official=1")
      .then(setWorkflows)
      .catch(console.error);
    api<GalleryItem[]>("/api/gallery").then(setGallery).catch(console.error);
  }, []);

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="animate-fade-up py-10 text-center">
        <h1 className="bg-gradient-to-r from-violet-500 via-purple-500 to-blue-500 bg-clip-text text-4xl font-bold text-transparent md:text-5xl">
          ComfyPortal
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-muted">
          自托管 ComfyUI 图像生成门户 —— 选工作流，填提示词，实时出图
        </p>
      </section>

      {/* 工作流 */}
      <section className="animate-fade-up">
        <h2 className="mb-4 text-xl font-semibold">预置工作流</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {workflows.map((w) => (
            <a
              key={w.id}
              href={`/create/${w.id}`}
              className="group rounded-xl border border-line bg-surface p-5 transition duration-200 hover:-translate-y-0.5 hover:border-accent"
            >
              <div className="font-medium">{w.name}</div>
              <div className="mt-1 text-sm text-muted">{w.description}</div>
            </a>
          ))}
        </div>
      </section>

      {/* 画廊 */}
      <section className="animate-fade-up">
        <h2 className="mb-4 text-xl font-semibold">画廊</h2>
        {gallery.length === 0 ? (
          <p className="text-sm text-muted">暂无作品，去选一个工作流生成吧</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
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
    </div>
  );
}
