import os
from celery import Celery

# Set default Django settings module for 'core'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Read config from Django settings using the 'CELERY' namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered app configs (e.g., tracker/tasks.py)
app.autodiscover_tasks()
