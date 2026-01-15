import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kids_App.settings")

celery = Celery("kids_App")
celery.config_from_object("django.conf:settings", namespaces="CELERY")
celery.autodiscovery_task()
