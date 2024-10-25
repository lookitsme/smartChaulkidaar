#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run Django management commands
python manage.py makemigrations
python manage.py migrate

# Run the Django development server
exec "$@"
