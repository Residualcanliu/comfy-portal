# Tailscale 组网（规格书 §1 架构 + §9 部署）

> 目标：本地 Windows 与 VPS 加入同一 tailnet，`ping` 通 tailnet IP 即完成组网。

## 本地 Windows

```powershell
winget install Tailscale.Tailscale
tailscale up   # 弹出浏览器，用 GitHub 账号登录
tailscale ip -4
```

## 阿里云 VPS

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
tailscale ip -4
```

## 验证

```bash
# 本地 → VPS
ping <VPS_TAILNET_IP>
# VPS → 本地
ping <LOCAL_TAILNET_IP>
```

- `TAILNET_IP` = VPS 的 tailnet IP，写入 deploy/.env（docker-compose 用它绑定 6379/8001/3000 到私有网卡）
- 安全组只开 22/tcp；Redis/PG/内部接口都走 tailnet，不暴露公网
