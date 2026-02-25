#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/vultr_bootstrap_ubuntu.sh"
  exit 1
fi

apt update
apt upgrade -y
apt install -y git curl nginx certbot python3-certbot-nginx ca-certificates

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  apt install -y docker-compose-plugin
fi

systemctl enable docker
systemctl start docker
systemctl enable nginx
systemctl start nginx

echo "Bootstrap complete."
echo "Next: clone repo, create .env, run docker compose with prod override."
