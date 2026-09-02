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
    <div className="space-y-10">
      <section>
        <h2 className="mb-4 text-xl font-semibold">预置工作流</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {workflows.map((w) => (
            <a
              key={w.id}
              href={`/create/${w.id}`}
              className="rounded-lg border border-zinc-800 p-4 transition hover:border-zinc-500"
            >
              <div className="font-medium">{w.name}</div>
              <div className="mt-1 text-sm text-zinc-400">{w.description}</div>
            </a>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold">画廊</h2>
        {gallery.length === 0 ? (
          <p className="text-sm text-zinc-500">暂无作品，去选一个工作流生成吧</p>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {gallery.map((g) => (
              <img
                key={g.id}
                src={`${API_URL}${g.url}`}
                alt={`作品 ${g.id}`}
                className="aspect-square rounded-lg object-cover"
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
