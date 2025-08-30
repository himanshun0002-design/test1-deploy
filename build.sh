#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Set environment variables for better performance
export GUNICORN_TIMEOUT=120
export GUNICORN_WORKERS=2
