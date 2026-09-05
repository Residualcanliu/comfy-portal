"""种子官方工作流（规格书 §2）。

运行（从 apps/api 目录，确保 .env 生效）：
    .venv/Scripts/python ../../scripts/seed_official_workflows.py
"""

import json
import os
import sys

# 让 app 包可导入（当前在 apps/api 下运行时，os.getcwd() 即 apps/api）
sys.path.insert(0, os.getcwd())

from app.db.session import SessionLocal
from app.models.workflow import Workflow

WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "workflows")

# 默认负面提示词（质量词；违规过滤词由 resolve_prompt_api 的 SAFETY_NEGATIVE 强制追加）
DEFAULT_NEGATIVE = (
    "low quality, worst quality, blurry, watermark, text, logo, jpeg artifacts, "
    "deformed, bad anatomy, extra limbs, extra fingers, mutated hands, "
    "poorly drawn face, bad proportions"
)

# 通用 slots（对应规格书 §2，节点 ID 与工作流 JSON 一致）
_BASE_SLOTS = [
    {"key": "prompt", "node": "6", "input": "text", "type": "text", "required": True, "label": "Prompt"},
    {"key": "negative_prompt", "node": "7", "input": "text", "type": "text", "default": DEFAULT_NEGATIVE, "label": "Negative"},
    {"key": "steps", "node": "3", "input": "steps", "type": "int", "min": 1, "max": 150, "default": 30, "label": "Steps"},
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
        "name": "SDXL 高清出图",
        "description": "1024×1024 高清，画质均衡",
        "prompt_api": _load("sdxl_txt2img.json"),
        "slots": _slots(cfg=6.0, steps=35),
        "model_refs": ["sd_xl_base_1.0_0.9vae.safetensors"],
    },
    {
        "name": "FLUX 顶级画质",
        "description": "细节最丰富，画质最好",
        "prompt_api": _load("flux_txt2img.json"),
        "slots": _slots(cfg=3.5),
        "model_refs": ["flux1-dev-fp8.safetensors"],
    },
    {
        "name": "SD1.5 极速出图",
        "description": "几秒一张，追求速度",
        "prompt_api": _load("sd15_gguf_txt2img.json"),
        "slots": _slots(steps=30, width=768, height=768),
        "model_refs": ["v1-5-pruned_Q8_0.gguf", "clip_l.safetensors", "vae-ft-mse-840000-ema-pruned.safetensors"],
    },
    # TODO(M1 后续)：img2img 放大（SDXL + 4x-UltraSharp）——需文件上传支持（W2）
]


def seed() -> None:
    db = SessionLocal()
    try:
        for wf in WORKFLOWS:
            exists = db.query(Workflow).filter(Workflow.name == wf["name"]).first()
            if exists:
                exists.description = wf["description"]
                exists.prompt_api = wf["prompt_api"]
                exists.slots = wf["slots"]
                exists.model_refs = wf["model_refs"]
                print(f"更新: {wf['name']}")
            else:
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
