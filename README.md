# Photoharu Server (Django)

## Quick start
1. Copy `.env.example` -> `.env`
2. Build and start:
```bash
docker compose up --build
```
3. Migrate:
```bash
docker compose exec web python manage.py migrate
```
4. Create admin:
```bash
docker compose exec web python manage.py createsuperuser
```
5. Open:
- Admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/api/docs/
- Health: http://localhost:8000/api/health/

## Make shortcuts
```bash
make up
make migrate
make superuser
```

## Production (Vultr + Cloudflare)
- Full guide: `docs/DEPLOY_VULTR_CLOUDFLARE.md`
- In production `.env`, set:
```env
WEB_BIND_HOST=127.0.0.1
WEB_PORT=8000
```
- Production compose:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Share Upload API (R2-ready)
- Required device auth headers:
  - `X-Device-Code`
  - `X-Device-Token`
- Endpoints:
  - `POST /api/kiosk/share/init`
  - `POST /api/kiosk/share/upload` (multipart: `token`, `kind`, `file`)
  - `POST /api/kiosk/share/finalize`
  - share page: `GET /s/<token>/`

### Environment variables (R2)
Add these to `.env`:
```env
SHARE_TOKEN_TTL_HOURS=24
PRESIGNED_EXPIRES_SECONDS=600
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=viorafilm
R2_PREFIX=sessions
```

If R2 values are missing, server falls back to local media storage.

### Alert settings (Email-first)
```env
ALERT_USE_SLACK=0
ALERT_NOTIFY_RECOVERY=1
ALERT_DAILY_REPORT_ENABLED=1
ALERT_DAILY_REPORT_HOUR=9
ALERT_DAILY_REPORT_MINUTE=0
OFFLINE_THRESHOLD_SECONDS=120
ALERT_NOTIFY_COOLDOWN_SECONDS=600
DEFAULT_FROM_EMAIL=noreply@photoharu.local
# Real SMTP (production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=YOUR_EMAIL@gmail.com
EMAIL_HOST_PASSWORD=YOUR_APP_PASSWORD
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_TIMEOUT=10
```
- Slack is disabled by default (`ALERT_USE_SLACK=0`).
- Recovery notifications can be enabled/disabled with `ALERT_NOTIFY_RECOVERY`.
- Daily ops report is sent by celery beat (`ALERT_DAILY_REPORT_*`).
- Configure recipients in Dashboard: `장치 관리 > 이메일 알림 설정`.
- Test delivery in Dashboard: `장치 관리 > 테스트 메일 발송`.
- Device issue alerts (offline/printer/camera/internet) will be sent to configured emails.

### Expired share cleanup
- Celery beat runs cleanup every 10 minutes.
- Expired share files are deleted from storage and expired share rows are removed.
- Manual run:
```bash
docker compose exec web python manage.py shell -c "from mediahub.tasks import cleanup_expired_shares; cleanup_expired_shares()"
```

### Curl test
```bash
curl -X POST http://localhost:8000/api/kiosk/share/init \
  -H "X-Device-Code: DEV" \
  -H "X-Device-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"test123\"}"

curl -X POST http://localhost:8000/api/kiosk/share/upload \
  -H "X-Device-Code: DEV" \
  -H "X-Device-Token: TOKEN" \
  -F "token=test123" \
  -F "kind=print" \
  -F "file=@D:/path/print.jpg"

curl -X POST http://localhost:8000/api/kiosk/share/finalize \
  -H "X-Device-Code: DEV" \
  -H "X-Device-Token: TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"test123\"}"
```

Then open:
- `http://localhost:8000/s/test123/`
