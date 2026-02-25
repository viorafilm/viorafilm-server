#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/opt/viorafilm-server}"

cd "${APP_DIR}"

if [[ ! -f .env ]]; then
  echo ".env not found in ${APP_DIR}"
  echo "Copy .env.example to .env and fill production values first."
  exit 1
fi

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "Deployment complete."
