#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Initialize MongoDB
python manage.py init_mongodb

# Run migrations for Django models
python manage.py migrate
