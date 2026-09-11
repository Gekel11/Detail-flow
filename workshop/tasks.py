from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone
from .models import ServiceOrder
from .services import generate_coating_certificate_pdf


@shared_task
def send_vehicle_ready_notification(order_id):
    order = ServiceOrder.objects.select_related('vehicle__owner').get(id=order_id)
    customer = order.vehicle.owner
    remaining_balance = order.price_total - (order.deposit_paid or 0)

    subject = f"Twój pojazd {order.vehicle.make} {order.vehicle.model} jest gotowy do odbioru! – DetailFlow"

    cert_info = ""
    certificate = getattr(order, 'coating_certificate', None)
    if order.requires_coating_certificate and certificate is not None:
        cert_info = (
            f"\nZabezpieczenie lakieru: {certificate.coating_product} "
            f"(Gwarancja: {certificate.warranty_months} mies.)\n"
            f"Oficjalny certyfikat załączono do niniejszej wiadomości w pliku PDF.\n"
        )

    body = (
        f"Cześć {customer.first_name},\n\n"
        f"Prace nad Twoim autem ({order.vehicle.make} {order.vehicle.model}, "
        f"rej. {order.vehicle.license_plate}) dobiegły końca!\n"
        f"Pakiet: {order.service_name}\n"
        f"{cert_info}\n"
        f"--- PODSUMOWANIE FINANSOWE ---\n"
        f"Wartość usługi: {order.price_total:.2f} PLN\n"
        f"Wpłacony zadatek: {order.deposit_paid or 0:.2f} PLN\n"
        f"DO ZAPŁATY PRZY ODBIORZE: {remaining_balance:.2f} PLN\n\n"
        f"Zapraszamy po odbiór samochodu do studia.\n"
        f"Zespół DetailFlow"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer.email],
    )

    if order.requires_coating_certificate and certificate is not None:
        try:
            pdf_bytes = generate_coating_certificate_pdf(certificate)
            filename = f"Certyfikat_{order.vehicle.license_plate}.pdf"
            email.attach(filename, pdf_bytes, 'application/pdf')
        except Exception as exc:
            print(f"Błąd generowania PDF: {exc}")

    email.send(fail_silently=False)
    return f"Wysłano powiadomienie dla zlecenia #{order.id}"


@shared_task
def send_evening_thank_you_discounts():
    """Wysyła maila z podziękowaniem i kodem -10% dla aut wydanych dzisiaj."""
    today = timezone.localdate()
    completed_today_orders = ServiceOrder.objects.filter(
        status='COMPLETED',
        completed_at__date=today,
    ).select_related('vehicle__owner')

    for order in completed_today_orders:
        customer = order.vehicle.owner
        subject = "Dziękujemy za wizytę w DetailFlow! Mamy dla Ciebie prezent"
        message = (
            f"Dzień dobry {customer.first_name},\n\n"
            f"Dziękujemy za zaufanie i powierzenie nam swojego "
            f"{order.vehicle.make} {order.vehicle.model}.\n"
            f"W ramach podziękowania przygotowaliśmy kod rabatowy -10% "
            f"na kolejną wizytę: DETAIL10\n\n"
            f"Do zobaczenia!\nZespół DetailFlow"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer.email],
            fail_silently=True,
        )
