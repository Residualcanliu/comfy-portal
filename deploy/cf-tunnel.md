# Cloudflare Tunnel（规格书 §1 安全姿态 + §9 部署）

> API 域名（api.*）走 CF Tunnel → 127.0.0.1:8000。VPS 出站连 CF，无需任何入站端口，也无需 ICP 备案。

## 步骤

```bash
# VPS 上
cloudflared tunnel login
cloudflared tunnel create comfy-portal
cloudflared tunnel route dns comfy-portal api.<domain>
# 记录 tunnel token → deploy/.env 的 CF_TUNNEL_TOKEN
```

- CORS 放行前端源（Vercel 域名）
- 静态图走 CF 橙色云缓存（免费 CDN，缓解 3M 带宽）
