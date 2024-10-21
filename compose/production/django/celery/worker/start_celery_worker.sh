#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Change to the directory where the Django project is located
cd /home/ubuntu/app_cunsole/compose/production/django  # Adjust if necessary

# Debug message
echo "Starting Celery Worker..." > /home/ubuntu/celery_worker.log 2>&1

# Set the PYTHONPATH and run the Celery worker, redirecting output to the log file
PYTHONPATH=/home/ubuntu/app_cunsole /home/ubuntu/app_cunsole/.venv/bin/celery -A config.celery_app worker -l INFO >> /home/ubuntu/celery_worker.log 2>&1

echo "Celery Worker started. Check the log file for details." >> /home/ubuntu/celery_worker.log 2>&1
