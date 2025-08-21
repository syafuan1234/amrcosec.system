#!/usr/bin/env bash
set -euo pipefail

echo "Applying database migrations…"
python manage.py migrate --noinput

echo "Collecting static files…"
python manage.py collectstatic --noinput

APP_MODULE=${APP_MODULE:-secretary.wsgi:application}

echo "Starting Gunicorn…"
exec gunicorn "$APP_MODULE" \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers ${WEB_CONCURRENCY:-3} \
  --threads ${WEB_THREADS:-2} \
  --timeout ${WEB_TIMEOUT:-120} \
  --access-logfile '-' --error-logfile '-'
