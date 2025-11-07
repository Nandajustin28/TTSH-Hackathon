#!/bin/bash
set -o errexit

echo "Running migrations..."
python manage.py migrate

echo "Enabling previous_status functionality..."
python manage.py enable_previous_status

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Deploy script completed successfully!"