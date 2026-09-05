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
    <div className="space-y-12">
      <section>
        <h2 className="mb-4 text-xl font-semibold">预置工作流</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {workflows.map((w) => (
            <a
              key={w.id}
              href={`/create/${w.id}`}
              className="group rounded-xl border border-line bg-surface p-5 transition hover:border-muted"
            >
              <div className="font-medium">{w.name}</div>
              <div className="mt-1 text-sm text-muted">{w.description}</div>
            </a>
          ))}
        </div>
      </section>

      <section>
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
                <div className="pointer-events-none absolute inset-0 bg-black/0 opacity-0 transition group-hover:bg-black/40 group-hover:opacity-100" />
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
