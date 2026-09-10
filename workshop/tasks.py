from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .models import ServiceOrder


@shared_task
def send_vehicle_ready_notification(order_id):
    order = ServiceOrder.objects.select_related('vehicle__owner').get(id=order_id)
    customer = order.vehicle.owner

    # Obliczenie kwoty do uregulowania
    remaining_balance = order.price_total - (order.deposit_paid or 0)

    subject = f"Twój pojazd {order.vehicle.make} {order.vehicle.model} jest gotowy do odbioru! – DetailFlow"

    message = (
        f"Cześć {customer.first_name},\n\n"
        f"Prace nad Twoim autem ({order.vehicle.make} {order.vehicle.model}, rej. {order.vehicle.license_plate}) dobiegły końca!\n"
        f"Pakiet: {order.service_name}\n\n"
        f"--- PODSUMOWANIE FINANSOWE ---\n"
        f"Wartość usługi: {order.price_total:.2f} PLN\n"
        f"Wpłacony zadatek: {order.deposit_paid or 0:.2f} PLN\n"
        f"DO ZAPŁATY PRZY ODBIORZE: {remaining_balance:.2f} PLN\n\n"
        f"Zapraszamy po odbiór samochodu do studia.\n"
        f"Zespół DetailFlow"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email="studio@detailflow.pl",
        recipient_list=[customer.email],
        fail_silently=False,
    )

    @shared_task
    def send_evening_thank_you_discounts():
        """Wysyła maila z podziękowaniem i kodem -10% dla aut wydanych dzisiaj"""
        today = timezone.now().date()

        # Szukamy zleceń wydanych dzisiaj
        completed_today_orders = ServiceOrder.objects.filter(
            status='COMPLETED',
            updated_at__date=today
        ).select_related('vehicle__owner')

        for order in completed_today_orders:
            customer = order.vehicle.owner
            subject = f"Dziękujemy za wizytę w DetailFlow! Mamy dla Ciebie prezent"
            message = (
                f"Dzień dobry {customer.first_name},\n\n"
                f"Dziękujemy za zaufanie i powierzenie nam swojego {order.vehicle.make} {order.vehicle.model}.\n"
                f"Mamy nadzieję, że efekt prac spełnia Twoje najwyższe oczekiwania!\n\n"
                f"W ramach podziękowania przygotowaliśmy dla Ciebie dedykowany rabat -10% na kolejną wizytę lub pielęgnację bieżącą:\n"
                f"KOD RABATOWY: DETAIL10\n\n"
                f"Do zobaczenia ponownie na hali!\n"
                f"Zespół DetailFlow"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email="studio@detailflow.pl",
                recipient_list=[customer.email],
                fail_silently=True,
            )