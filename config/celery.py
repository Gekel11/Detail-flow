import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-thank-you-discounts-at-20': {
        'task': 'workshop.tasks.send_evening_thank_you_discounts',
        'schedule': crontab(hour=20, minute=0),
    },
}