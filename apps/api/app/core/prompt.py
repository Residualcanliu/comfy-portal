"""工作流参数注入（规格书 §2：按 slots 把用户参数注入 prompt_api 对应 node.inputs）。"""

from __future__ import annotations

import copy
import random
from typing import Any


def resolve_prompt_api(
    prompt_api: dict[str, Any], slots: list[dict[str, Any]], params: dict[str, Any]
) -> dict[str, Any]:
    """把用户提交的 params 按 slots 注入到 ComfyUI API 格式的 prompt_api 中。

    ComfyUI API 格式：{"<node_id>": {"class_type": ..., "inputs": {...}}, ...}
    seed 槽位值为 -1 或缺失时替换为随机值。
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

        node_id = slot.get("node")
        input_name = slot.get("input")
        if node_id in resolved and "inputs" in resolved[node_id]:
            resolved[node_id]["inputs"][input_name] = value

    return resolved
