"""工作流参数注入（规格书 §2：按 slots 把用户参数注入 prompt_api 对应 node.inputs）。"""

from __future__ import annotations

import copy
import random
from typing import Any

# 违规内容硬性过滤：无论用户/默认值怎么填，都强制追加到负面提示词，
# 阻止色情 / 暴力 / 血腥 / 仇恨等违规生成。
SAFETY_NEGATIVE = (
    "nudity, naked, nude, nsfw, explicit, porn, pornographic, sex, sexual, "
    "erotic, hentai, lewd, exposed breasts, exposed genitals, genitalia, "
    "violence, gore, blood, weapon, gun, hate symbol, racism, offensive, "
    "adult content, 18+, 裸体, 色情, 淫秽"
)

# 用户 prompt 违规词（命中即拒绝提交，大小写不敏感，中英文）
BANNED_PROMPT_WORDS = (
    "nude", "naked", "nudity", "nsfw", "porn", "pornographic", "sex", "sexual",
    "explicit", "hentai", "erotic", "lewd", "adult content", "裸体", "裸照",
    "色情", "黄图", "淫秽", "成人", "性交", "做爱",
)


def check_prompt(prompt: str) -> bool:
    """检测 prompt 是否含违规词，命中返回 True。"""
    lowered = prompt.lower()
    return any(word in lowered for word in BANNED_PROMPT_WORDS)


def resolve_prompt_api(
    prompt_api: dict[str, Any], slots: list[dict[str, Any]], params: dict[str, Any]
) -> dict[str, Any]:
    """把用户提交的 params 按 slots 注入到 ComfyUI API 格式的 prompt_api 中。

    ComfyUI API 格式：{"<node_id>": {"class_type": ..., "inputs": {...}}, ...}
    seed 槽位值为 -1 或缺失时替换为随机值。
    负面提示词会强制追加 SAFETY_NEGATIVE（违规过滤），用户无法覆盖。
    """
    resolved = copy.deepcopy(prompt_api)

    for slot in slots:
        key = slot.get("key")
        value = params.get(key, slot.get("default"))

        slot_type = slot.get("type")
        if slot_type == "int":
            value = int(value)
        elif slot_type == "float":
            value = float(value)

        if key == "seed" and (value is None or value == -1):
            value = random.randint(0, 2**31 - 1)

        # 负面提示词：拼接安全过滤词（即使 value 为空也至少包含 SAFETY_NEGATIVE）
        if key == "negative_prompt":
            base = value if isinstance(value, str) else ""
            value = f"{base}, {SAFETY_NEGATIVE}".strip(", ")

        node_id = slot.get("node")
        input_name = slot.get("input")
        if node_id in resolved and "inputs" in resolved[node_id]:
            resolved[node_id]["inputs"][input_name] = value

    return resolved
