#!/usr/bin/env bash
# ComfyPortal VPS 一键初始化（Ubuntu 22.04，规格书 §9）
set -euo pipefail

echo "==> 安装 docker / ufw"
apt update
apt install -y docker.io docker-compose-v2 ufw

echo "==> 防火墙：只开 22/tcp（唯一入站端口）"
ufw allow 22/tcp
ufw --force enable

echo "==> 4G swap 兜底"
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> 后续步骤（见 deploy/tailscale.md / cf-tunnel.md）"
echo "  1. tailscale up --ssh   → 记录 TAILNET_IP"
echo "  2. cloudflared tunnel 配置 → CF_TUNNEL_TOKEN 写入 .env"
echo "  3. git clone → /srv/comfy-portal → cp .env.example .env → docker compose up -d"
