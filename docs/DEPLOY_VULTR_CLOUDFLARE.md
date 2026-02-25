# Viorafilm Production Deploy (Vultr + Cloudflare)

This guide is for first production setup.

## 1) Create VPS on Vultr
1. Vultr dashboard -> `Deploy` -> `Cloud Compute`.
2. Region: closest to your kiosk users.
3. Image: `Ubuntu 22.04 LTS`.
4. Plan: start with `2 vCPU / 4 GB RAM`.
5. Authentication: SSH key recommended.
6. Create server and copy public IPv4.

## 2) Connect domain in Cloudflare
1. Cloudflare -> `viorafilm.com` -> DNS.
2. Add `A` record:
   - Name: `api`
   - IPv4: `<your_vps_ip>`
   - Proxy status: `DNS only` (gray cloud) for first setup.

## 3) Login VPS and install base packages
```bash
ssh root@<your_vps_ip>
```

Run:
```bash
apt update && apt upgrade -y
apt install -y git curl nginx certbot python3-certbot-nginx ca-certificates
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin
systemctl enable --now docker
systemctl enable --now nginx
```

## 4) Pull project from GitHub
```bash
cd /opt
git clone https://github.com/viorafilm/viorafilm-server.git
cd /opt/viorafilm-server
cp .env.example .env
```

## 5) Fill production `.env`
Set at least:
- `DEBUG=0`
- `ALLOWED_HOSTS=api.viorafilm.com`
- `CSRF_TRUSTED_ORIGINS=https://api.viorafilm.com`
- `SESSION_COOKIE_SECURE=1`
- `CSRF_COOKIE_SECURE=1`
- `SECURE_SSL_REDIRECT=0` (Nginx handles HTTPS redirect with certbot)
- R2 values:
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
  - `R2_BUCKET_NAME=viorafilm`
  - `R2_PREFIX=sessions`

## 6) Run containers (prod override)
```bash
cd /opt/viorafilm-server
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## 7) Nginx reverse proxy
```bash
cp /opt/viorafilm-server/deploy/nginx/api.viorafilm.com.conf /etc/nginx/sites-available/api.viorafilm.com.conf
ln -s /etc/nginx/sites-available/api.viorafilm.com.conf /etc/nginx/sites-enabled/api.viorafilm.com.conf
nginx -t
systemctl reload nginx
```

## 8) TLS certificate (HTTPS)
```bash
certbot --nginx -d api.viorafilm.com
```

## 9) Verify
- `https://api.viorafilm.com/api/health/`
- `https://api.viorafilm.com/admin/`
- `https://api.viorafilm.com/api/docs/`
- `https://api.viorafilm.com/dashboard/login`

## 10) Update flow after code changes
On local PC:
```bash
git add .
git commit -m "your update"
git push origin main
```

On VPS:
```bash
cd /opt/viorafilm-server
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
```
