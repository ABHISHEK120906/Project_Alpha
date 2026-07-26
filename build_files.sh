#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --noinput

# Run database migrations (Neon PostgreSQL)
python manage.py migrate --noinput
