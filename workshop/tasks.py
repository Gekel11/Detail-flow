from celery import shared_task
from .services import NotificationService

@shared_task(name="tasks.send_vehicle_ready_notification")
def send_vehicle_ready_notification(order_id: int):
    return NotificationService.send_order_ready_email(order_id)