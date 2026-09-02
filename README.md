# ComfyPortal

自托管 ComfyUI 图像生成 Web 门户：上传工作流 → 排队生成 → 实时看进度 → 作品画廊。

> 完整工程规格见仓库外的 `项目.md`（§0–§16）。本文档只记录代码层面的关键信息。

## 架构一句话

**控制面 / GPU 分离**：Next.js 前端（Vercel）+ FastAPI 控制面（阿里云 2C2G VPS，24/7）+ Redis/RQ 队列 + 本地 4090D 生成节点，SSE 实时进度，Prometheus/Grafana 监控，多用户 + 日配额。

```
浏览器 ─HTTPS─▶ Vercel(Next.js) ─api域名(CF Tunnel)─▶ VPS(FastAPI/Redis/PG/Prom/Grafana)
                                                        ▲ Tailscale 私有网
本地 Windows 4090D(ComfyUI + RQ worker) ──压缩上传──▶ VPS /internal/artifacts/upload
```

## 仓库结构

```
apps/web      # Next.js 15 App Router + TS + Tailwind（Vercel）
apps/api      # FastAPI + SQLAlchemy2 + alembic（VPS docker）
apps/worker   # RQ worker（本地 Windows）：comfy client/重试/上传/心跳/metrics
packages/shared# 任务状态机 + SSE 事件 schema + DTO（pydantic + TS 双份，接口变更必须同步）
deploy/       # docker-compose / prometheus / grafana / vps-setup / 组网与迁移文档
scripts/      # bench_gguf / loadtest / seed / 模型下载
```

## 本地开发

```bash
# Python 侧（api / worker 各自 venv，共享包 editable 安装）
cd packages/shared/python && pip install -e .
cd apps/api && pip install -e .[dev]
cd apps/worker && pip install -e .[dev]

# Web 侧
npm install          # 根目录，安装 workspaces
npm run dev:web
```

## 关键约定（详见项目.md §16）

- 文档语言中文，代码/标识符英文；conventional commits
- 接口变更必须同步 `packages/shared`（py + ts 双份）
- 每个 env 配 `.env.example`；每里程碑核心路径有测试；W1 结束前 CI 必须绿
