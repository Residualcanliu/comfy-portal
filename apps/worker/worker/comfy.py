"""ComfyUI 客户端：POST /prompt + ws 跟踪进度（规格书 §6）。"""

from __future__ import annotations

from collections.abc import Callable
import json
from urllib.parse import urlparse
import uuid

import httpx
from websockets.sync.client import connect

from worker.config import settings


def _ws_url() -> str:
    u = urlparse(settings.comfyui_url)
    scheme = "wss" if u.scheme == "https" else "ws"
    return f"{scheme}://{u.netloc}/ws"


def submit_prompt(prompt_api: dict) -> tuple[str, str]:
    """POST /prompt，返回 (prompt_id, client_id)。"""
    client_id = uuid.uuid4().hex
    resp = httpx.post(
        f"{settings.comfyui_url}/prompt",
        json={"prompt": prompt_api, "client_id": client_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"], client_id


def track_progress(
    client_id: str,
    on_progress: Callable[[float, str, int, int], None],
) -> list[dict]:
    """连接 ws 跟踪进度，返回收集到的 image 输出列表（filename/subfolder/type）。"""
    images: list[dict] = []
    current_node = ""
    step, max_steps = 0, 1

    with connect(f"{_ws_url()}?clientId={client_id}", open_timeout=30) as ws:
        for raw in ws:
            msg = json.loads(raw)
            mtype = msg.get("type")
            data = msg.get("data", {})
            if mtype == "progress":
                # 直接用 KSampler 步数进度 0→100%，不依赖节点完成计数（更可靠）
                step = int(data.get("value", 0))
                max_steps = max(int(data.get("max", 1)), 1)
                pct = step / max_steps * 100
                on_progress(min(pct, 100.0), current_node or "KSampler", step, max_steps)
            elif mtype == "executing":
                if data.get("node"):
                    current_node = data["node"]
            elif mtype == "executed":
                images.extend(data.get("output", {}).get("images", []))
            elif mtype == "execution_success":
                break
            elif mtype == "execution_error":
                raise RuntimeError(json.dumps(data))

    return images


def fetch_image(image: dict) -> bytes:
    """通过 ComfyUI /view 拉取产物原图。"""
    resp = httpx.get(
        f"{settings.comfyui_url}/view",
        params={
            "filename": image["filename"],
            "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output"),
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content
