from django.core.mail import send_mail
from django.conf import settings
from .models import ServiceOrder

class NotificationService:
    @staticmethod
    def send_order_ready_email(order_id: int) -> bool:
        try:
            order = ServiceOrder.objects.select_related('vehicle__owner').get(id=order_id)
            customer = order.vehicle.owner

            subject = f"Twój pojazd jest gotowy do odbioru! [{order.vehicle.license_plate}]"
            message = (
                f"Cześć {customer.first_name},\n\n"
                f"Prace nad Twoim samochodem ({order.vehicle.make} {order.vehicle.model}) zostały zakończone.\n"
                f"Usługa: {order.service_name}\n"
                f"Pozostała kwota do zapłaty: {order.price_total - order.deposit_paid} PLN.\n\n"
                f"Zapraszamy po odbiór auta do studia!\n"
                f"Zespół DetailFlow"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email='powiadomienia@detailflow.local',
                recipient_list=[customer.email],
                fail_silently=False,
            )
            return True
        except ServiceOrder.DoesNotExist:
            return False