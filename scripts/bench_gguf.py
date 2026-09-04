"""bench_gguf.py：SDXL fp16 vs GGUF Q8 A/B 基准（规格书 §8 + §12）。

固定 SDXL 工作流（1024², steps=20, cfg=7, seed=42），各 20 次，
记录 wall time + 峰值显存（轮询 /system_stats），输出 markdown 表（mean/p50/p95/peak_vram/Δ）。

用法：python scripts/bench_gguf.py
"""

import json
import statistics
import time
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
ITERATIONS = 20
TIMEOUT = 300  # 单次生成超时（秒）

PROMPT = "a photo of a majestic lion in a golden savanna at sunrise, ultra detailed"
NEGATIVE = "low quality, blurry, watermark"

# SDXL fp16（CheckpointLoaderSimple 全精度，UNET+CLIP+VAE 打包）
FP16_WORKFLOW = {
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0_0.9vae.safetensors"}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["4", 1]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["4", 1]}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "3": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
        "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
    }},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "bench_fp16", "images": ["8", 0]}},
}

# SDXL GGUF Q8_0（UnetLoaderGGUF + 单独 CLIP/VAE）
# TODO: 下载完成后验证 CLIP 加载（SDXL 可能需要 dual clip-l+clip-g）
GGUF_WORKFLOW = {
    "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "sd_xl_base_1.0_0_Q8_0.gguf"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "clip_l.safetensors", "type": "stable_diffusion"}},
    "4": {"class_type": "VAELoader", "inputs": {"vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["2", 0]}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "3": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
        "model": ["1", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
    }},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "bench_gguf", "images": ["8", 0]}},
}


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
    d = _get("/system_stats")
    dev = d["devices"][0]
    return dev["vram_total"] - dev["vram_free"]


def _submit(wf: dict) -> str:
    return _post("/prompt", {"prompt": wf, "client_id": uuid.uuid4().hex})["prompt_id"]


def _wait_done(prompt_id: str) -> tuple[float, int]:
    """轮询 /history 直到完成，返回 (wall_time, peak_vram)。"""
    t0 = time.time()
    peak_vram = 0
    while True:
        time.sleep(0.5)
        peak_vram = max(peak_vram, _vram_used())
        h = _get(f"/history/{prompt_id}")
        if prompt_id in h:
            st = h[prompt_id].get("status", {}).get("status_str")
            if st == "success":
                return time.time() - t0, peak_vram
            if st == "error":
                raise RuntimeError(f"生成失败: {prompt_id}")
        if time.time() - t0 > TIMEOUT:
            raise TimeoutError(f"超时: {prompt_id}")


def _bench(wf: dict, name: str) -> tuple[list[float], list[int]]:
    times, vrams = [], []
    for i in range(ITERATIONS):
        pid = _submit(wf)
        t, v = _wait_done(pid)
        times.append(t)
        vrams.append(v)
        print(f"  {name} {i + 1}/{ITERATIONS}: {t:.2f}s  peak_vram {v / 1024:.0f}MB")
    return times, vrams


def _p95(xs: list[float]) -> float:
    return sorted(xs)[int(len(xs) * 0.95) - 1]


def main() -> None:
    print(f"=== SDXL fp16 基准（{ITERATIONS} 次）===")
    t16, v16 = _bench(FP16_WORKFLOW, "fp16")
    print(f"=== SDXL GGUF Q8_0 基准（{ITERATIONS} 次）===")
    t8, v8 = _bench(GGUF_WORKFLOW, "GGUF")

    def fmt(fn, a, b):
        x, y = fn(a), fn(b)
        return f"{x:.2f} | {y:.2f} | {x - y:+.2f}"

    print("\n| 指标 | fp16 | GGUF Q8 | Δ |")
    print("|---|---|---|---|")
    print(f"| 平均耗时 (s) | {fmt(statistics.mean, t16, t8)} |")
    print(f"| P50 耗时 (s) | {fmt(statistics.median, t16, t8)} |")
    print(f"| P95 耗时 (s) | {fmt(_p95, t16, t8)} |")
    m16, m8 = statistics.mean(v16) / 1024, statistics.mean(v8) / 1024
    print(f"| 峰值显存均值 (MB) | {m16:.0f} | {m8:.0f} | {m16 - m8:+.0f} |")


if __name__ == "__main__":
    main()
