

# import os
# from celery import Celery

# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# # Create a new Celery app instance
# app = Celery("app_cunsole")

# # Load task modules from all registered Django app configs.
# app.config_from_object("django.conf:settings", namespace="CELERY")

# # Auto-discover tasks in all registered apps.
# app.autodiscover_tasks()


import os
from celery import Celery




# Determine the correct settings module based on the environment variable
# env = os.environ.get("DJANGO_ENV", "local")  # Default to 'local' if not set
env = os.environ.get("DJANGO_ENV", "production")  # Default to 'local' if not set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{env}")

# Create a new Celery app instance
app = Celery("app_cunsole")

# Load task modules from all registered Django app configs
app.config_from_object("django.conf:settings", namespace="CELERY")




# Auto-discover tasks in all registered apps
app.autodiscover_tasks()
