# import os

# from celery import Celery

# # set the default Django settings module for the 'celery' program.
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# app = Celery("app_cunsole")

# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# # - namespace='CELERY' means all celery-related configuration keys
# #   should have a `CELERY_` prefix.
# app.config_from_object("django.conf:settings", namespace="CELERY")

# # Load task modules from all registered Django app configs.
# app.autodiscover_tasks()


import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Create a new Celery app instance
app = Celery("app_cunsole")

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all registered apps.
app.autodiscover_tasks()
