"""bench_models.py：三个官方工作流的出图耗时 + 显存基准（规格书 §8）。

直接打 ComfyUI（127.0.0.1:8188），跳过队列/API，测的是纯模型出图速度。
参数与线上 seed 的 slot 默认值一致，结果可直接用于 README / 简历。

用法（先确保 ComfyUI 已启动）：
    python scripts/bench_models.py          # 每个模型 5 次
    python scripts/bench_models.py 10       # 每个模型 10 次
"""

import json
import os
import statistics
import sys
import time
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
TIMEOUT = 900  # 单次生成超时（秒）
ITERATIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 5

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")

PROMPT = "a photo of a majestic lion in a golden savanna at sunrise, ultra detailed"

MODELS = [
    {
        "name": "SD1.5 GGUF Q8",
        "file": "sd15_gguf_txt2img.json",
        "steps": 30,
        "cfg": 7.0,
        "width": 768,
        "height": 768,
    },
    {
        "name": "SDXL fp16",
        "file": "sdxl_txt2img.json",
        "steps": 35,
        "cfg": 6.0,
        "width": 1024,
        "height": 1024,
    },
    {
        "name": "FLUX.1-dev fp8",
        "file": "flux_txt2img.json",
        "steps": 30,
        "cfg": 3.5,
        "width": 1024,
        "height": 1024,
    },
]


def _load(name: str) -> dict:
    with open(os.path.join(WORKFLOWS_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _post(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        f"{COMFY}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def _get(path: str) -> dict:
    return json.loads(urllib.request.urlopen(f"{COMFY}{path}", timeout=30).read())


def _vram_used() -> int:
    dev = _get("/system_stats")["devices"][0]
    return dev["vram_total"] - dev["vram_free"]


def _free_models() -> None:
    """卸载已缓存模型，让每个模型的显存基线干净（否则读到的是所有模型的缓存总和）。"""
    req = urllib.request.Request(
        f"{COMFY}/free",
        data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=30).read()
    time.sleep(3)  # 等显存真正回收


def _wait_done(prompt_id: str) -> tuple[float, int]:
    """轮询 /history 直到完成，返回 (wall_time, peak_vram)。"""
    t0 = time.time()
    peak = 0
    while True:
        time.sleep(0.5)
        peak = max(peak, _vram_used())
        h = _get(f"/history/{prompt_id}")
        if prompt_id in h:
            st = h[prompt_id].get("status", {}).get("status_str")
            if st == "success":
                return time.time() - t0, peak
            if st == "error":
                raise RuntimeError(f"生成失败: {prompt_id}")
        if time.time() - t0 > TIMEOUT:
            raise TimeoutError(f"超时: {prompt_id}")


def _build(model: dict) -> dict:
    """按线上 slot 默认值构造工作流（改 3=KSampler, 5=Latent, 6/7=prompt）。"""
    wf = _load(model["file"])
    wf["3"]["inputs"]["steps"] = model["steps"]
    wf["3"]["inputs"]["cfg"] = model["cfg"]
    wf["5"]["inputs"]["width"] = model["width"]
    wf["5"]["inputs"]["height"] = model["height"]
    wf["6"]["inputs"]["text"] = PROMPT
    return wf


def _bench_one(model: dict) -> tuple[list[float], list[int], int]:
    _free_models()
    baseline = _vram_used()  # 空载基线，用于算模型真实占用
    times: list[float] = []
    vrams: list[int] = []
    for i in range(ITERATIONS):
        wf = _build(model)
        wf["3"]["inputs"]["seed"] = 42 + i  # 换 seed，避免缓存命中
        pid = _post("/prompt", {"prompt": wf, "client_id": uuid.uuid4().hex})["prompt_id"]
        t, v = _wait_done(pid)
        times.append(t)
        vrams.append(v)
        tag = "冷启动" if i == 0 else f"第{i + 1}次"
        print(
            f"  {tag}: {t:.2f}s  峰值显存 {v / 1024 / 1024:.0f}MB "
            f"(净增 {(v - baseline) / 1024 / 1024:.0f}MB)",
            flush=True,
        )
    return times, vrams, baseline


def main() -> None:
    print(f"=== ComfyPortal 模型基准（每个 {ITERATIONS} 次）===\n")
    results = []
    for m in MODELS:
        print(f"--- {m['name']}  {m['width']}×{m['height']}  steps={m['steps']} ---")
        times, vrams, baseline = _bench_one(m)
        results.append((m, times, vrams, baseline))
        print()

    print("| 模型 | 分辨率 | 冷启动 (s) | 热态 P50 (s) | 平均 (s) | 峰值显存 (MB) |")
    print("|---|---|---|---|---|---|")
    for m, times, vrams, baseline in results:
        cold = times[0]
        warm = times[1:] or times
        peak = statistics.mean(vrams) / 1024 / 1024
        print(
            f"| {m['name']} | {m['width']}×{m['height']} | {cold:.1f} | "
            f"{statistics.median(warm):.1f} | {statistics.mean(times):.1f} | "
            f"{peak:.0f} |"
        )


if __name__ == "__main__":
    main()
