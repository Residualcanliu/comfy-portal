# ComfyPortal API 镜像（build context = 仓库根，见 deploy/docker-compose.yml）
FROM python:3.11-slim

WORKDIR /app

# 复制 shared 契约包 + api 应用（shared 是本地依赖，必须一起打进去）
COPY packages/shared/python /app/packages/shared/python
COPY apps/api /app/apps/api

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple /app/packages/shared/python
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple /app/apps/api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
