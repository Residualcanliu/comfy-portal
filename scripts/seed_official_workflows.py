"""种子官方工作流（规格书 §2）。

运行（从 apps/api 目录，确保 .env 生效）：
    .venv/Scripts/python ../../scripts/seed_official_workflows.py
"""

import json
import os
import sys

# 让 app 包可导入（当前在 apps/api 下运行时，os.getcwd() 即 apps/api）
sys.path.insert(0, os.getcwd())

from app.db.session import SessionLocal  # noqa: E402
from app.models.workflow import Workflow  # noqa: E402

WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "workflows")

# 通用 slots（对应规格书 §2，节点 ID 与工作流 JSON 一致）
_BASE_SLOTS = [
    {"key": "prompt", "node": "6", "input": "text", "type": "text", "required": True, "label": "Prompt"},
    {"key": "negative_prompt", "node": "7", "input": "text", "type": "text", "label": "Negative"},
    {"key": "steps", "node": "3", "input": "steps", "type": "int", "min": 1, "max": 150, "default": 20, "label": "Steps"},
    {"key": "cfg", "node": "3", "input": "cfg", "type": "float", "min": 0, "max": 30, "default": 7.0, "label": "CFG"},
    {"key": "seed", "node": "3", "input": "seed", "type": "int", "default": -1, "label": "Seed(-1随机)"},
    {"key": "width", "node": "5", "input": "width", "type": "int", "default": 1024, "label": "Width"},
    {"key": "height", "node": "5", "input": "height", "type": "int", "default": 1024, "label": "Height"},
]


def _slots(**overrides):
    slots = [dict(s) for s in _BASE_SLOTS]
    for key, value in overrides.items():
        for s in slots:
            if s["key"] == key:
                s["default"] = value
    return slots


def _load(name):
    with open(os.path.join(WORKFLOWS_DIR, name), encoding="utf-8") as f:
        return json.load(f)


WORKFLOWS = [
    {
        "name": "SDXL 文生图（fp16）",
        "description": "质量基线，1024×1024，fp16 全精度",
        "prompt_api": _load("sdxl_txt2img.json"),
        "slots": _slots(cfg=7.0),
        "model_refs": ["sd_xl_base_1.0_0.9vae.safetensors"],
    },
    {
        "name": "FLUX.1-dev（fp8）",
        "description": "高质量文生图，fp8 量化，24GB 可跑",
        "prompt_api": _load("flux_txt2img.json"),
        "slots": _slots(cfg=3.5),
        "model_refs": ["flux1-dev-fp8.safetensors"],
    },
    # TODO(M1 后续)：SD1.5 文生图（GGUF Q8）——需补 VAE + CLIP
    # TODO(M1 后续)：img2img 放大（SDXL + 4x-UltraSharp）
]


def seed() -> None:
    db = SessionLocal()
    try:
        for wf in WORKFLOWS:
            exists = db.query(Workflow).filter(Workflow.name == wf["name"]).first()
            if exists:
                print(f"跳过（已存在）: {wf['name']}")
                continue
            db.add(
                Workflow(
                    user_id=None,
                    is_official=True,
                    name=wf["name"],
                    description=wf["description"],
                    prompt_api=wf["prompt_api"],
                    slots=wf["slots"],
                    model_refs=wf["model_refs"],
                )
            )
            print(f"已种子: {wf['name']}")
        db.commit()
        print("种子完成")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
