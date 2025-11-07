#!/bin/bash
set -o errexit

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Deploy script completed successfully!"