"""按 models.txt 下载模型（~20GB）。

用法：
    python scripts/download_models.py [--target D:\\ComfyUI\\models] [--mirror hf-mirror.com]

TODO(M1): 解析 models.txt，用 huggingface_hub 下载到 ComfyUI 对应子目录，
支持断点续传 + hf-mirror 镜像（国内网络）。下载后校验文件存在（worker 启动核对 model_refs）。
"""
