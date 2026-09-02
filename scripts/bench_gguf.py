"""GGUF vs fp16 基准（规格书 §8 + §12）。

固定 SDXL 工作流（1024², steps=20, cfg=7, seed=42），fp16(UNETLoader) vs GGUF Q8(UnetLoaderGGUF)
各 20 次；每次记录 wall time + 轮询 /system_stats 取峰值显存 + 输出 sha256 校验；
输出 markdown 表（mean/p50/p95/peak_vram/Δ）。

TODO(M2): 实现。
"""
