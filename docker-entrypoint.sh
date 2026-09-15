#!/bin/sh
set -e

echo ">> DetailFlow: migrate..."
python manage.py migrate --noinput

echo ">> DetailFlow: seed demo (idempotent)..."
python manage.py seed_demo

exec "$@"
