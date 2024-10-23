

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
from dotenv import load_dotenv
from celery import Celery

# Load environment variables from .env file
load_dotenv()

# Set the default Django settings module for the 'celery' program.
env = os.getenv("DJANGO_ENV", "local")  # Default to 'local' if not set
if env == "production":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Create a new Celery app instance
app = Celery("app_cunsole")

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all registered apps.
app.autodiscover_tasks()
