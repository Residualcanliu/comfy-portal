# ComfyPortal API 镜像。
# TODO(M4): 完善 —— 需把 packages/shared 纳入 build（当前 build context 为 apps/api，
#           M4 阶段将 context 提到仓库根、改用 dockerfile 路径，并处理 shared 依赖）。
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
