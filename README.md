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
