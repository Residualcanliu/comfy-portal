"""RQ 任务：run_job（规格书 §6 全流程）。"""

from __future__ import annotations

import json
from io import BytesIO

import httpx
import redis
from PIL import Image

from worker.comfy import fetch_image, submit_prompt, track_progress
from worker.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
_HEADERS = {"X-Internal-Token": settings.internal_token}


def _publish(task_id: int, event: str, data: dict) -> None:
    redis_client.publish(f"task:{task_id}", json.dumps({"event": event, "data": data}))


def _report_state(
    task_id: int,
    state: str,
    error: str | None = None,
    comfy_prompt_id: str | None = None,
) -> None:
    httpx.post(
        f"{settings.api_internal_url}/internal/tasks/{task_id}/state",
        headers=_HEADERS,
        json={"state": state, "error": error, "comfy_prompt_id": comfy_prompt_id},
        timeout=30,
    ).raise_for_status()


def _compress(data: bytes, max_edge: int = 1536, quality: int = 85) -> tuple[bytes, int, int]:
    """Pillow 压缩（规格书 §1：JPEG q85，长边 ≤1536px，<1MB）。"""
    img = Image.open(BytesIO(data)).convert("RGB")
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue(), img.size[0], img.size[1]


def run_job(task_id: int, prompt_api: dict) -> dict:
    """RQ 入口（API 通过 "worker.main.run_job" 入队调用）。"""
    try:
        prompt_id, client_id = submit_prompt(prompt_api)
        _report_state(task_id, "running", comfy_prompt_id=prompt_id)

        def on_progress(pct: float, node: str, step: int, max_steps: int) -> None:
            # 更新 last_activity（TTL 600s=10min，供 API 陈旧恢复判断）
            redis_client.set(f"task:{task_id}:last_activity", "1", ex=600)
            _publish(
                task_id,
                "progress",
                {"pct": pct, "node": node, "step": step, "max_steps": max_steps},
            )

        images = track_progress(client_id, on_progress)

        artifacts = []
        for img in images:
            raw = fetch_image(img)
            compressed, w, h = _compress(raw)
            resp = httpx.post(
                f"{settings.api_internal_url}/internal/artifacts/upload",
                headers=_HEADERS,
                data={
                    "task_id": str(task_id),
                    "kind": "image",
                    "width": str(w),
                    "height": str(h),
                },
                files={"file": ("output.jpg", compressed, "image/jpeg")},
                timeout=60,
            )
            resp.raise_for_status()
            up = resp.json()
            artifacts.append(
                {"id": up["id"], "kind": "image", "url": up["url"], "width": w, "height": h}
            )

        _report_state(task_id, "success")
        _publish(task_id, "done", {"state": "success", "artifacts": artifacts})
        return {"task_id": task_id, "artifacts": artifacts}
    except Exception as e:
        _report_state(task_id, "failed", error=str(e))
        _publish(task_id, "error", {"state": "failed", "error": str(e)})
        raise
