#!/bin/bash
set -e

echo "=== Running collectstatic ==="
python manage.py collectstatic --noinput

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Starting gunicorn ==="
gunicorn ditaboutique.wsgi --bind 0.0.0.0:$PORT
