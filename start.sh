#!/usr/bin/env bash

# Start Gunicorn with optimized settings
gunicorn registration_project.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
