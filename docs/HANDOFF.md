# Handoff

## Current Snapshot
- R2-based upload pipeline is working (`share/init`, `share/upload`, `share/finalize`).
- Share page `/s/<token>/` serves presigned R2 URLs.
- Cleanup job exists for expired shares.
- Dashboard modules exist; parity polishing remains.

## Immediate Next Action
1. Move to production-safe env:
   - set `DEBUG=0`
   - regenerate `SECRET_KEY`
   - set production `ALLOWED_HOSTS`
2. Rebuild/restart containers and re-run smoke tests.

## Last Verified Commands
- `docker compose up -d --build web celery_worker celery_beat`
- `docker compose exec web python manage.py migrate`
- `docker compose exec web python manage.py check`

## Risks
- Exposed credentials in prior chat history must be rotated.
- Some modules still show migration drift warnings in certain branches; always run `makemigrations` check before release.
