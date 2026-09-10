from celery import shared_task
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
    if order.requires_coating_certificate and hasattr(order, 'coating_certificate'):
        cert = order.coating_certificate
        cert_info = f"\nZabezpieczenie lakieru: {cert.coating_product} (Gwarancja: {cert.warranty_months} mies.)\nOficjalny certyfikat załączono do niniejszej wiadomości w pliku PDF.\n"

    body = (
        f"Cześć {customer.first_name},\n\n"
        f"Prace nad Twoim autem ({order.vehicle.make} {order.vehicle.model}, rej. {order.vehicle.license_plate}) dobiegły końca!\n"
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
        from_email="studio@detailflow.pl",
        to=[customer.email],
    )

    # Dołącz PDF tylko, jeśli zlecenie obejmuje ceramikę i certyfikat istnieje!
    if order.requires_coating_certificate and hasattr(order, 'coating_certificate'):
        try:
            pdf_bytes = generate_coating_certificate_pdf(order.coating_certificate)
            filename = f"Certyfikat_{order.vehicle.license_plate}.pdf"
            email.attach(filename, pdf_bytes, 'application/pdf')
        except Exception as e:
            print(f"Błąd generowania PDF: {e}")

    email.send(fail_silently=False)
    return f"Wysłano powiadomienie dla zlecenia #{order.id}"


@shared_task
def send_evening_thank_you_discounts():
    """Wysyła maila z podziękowaniem i kodem -10% dla aut wydanych dzisiaj"""
    today = timezone.now().date()
    completed_today_orders = ServiceOrder.objects.filter(
        status='COMPLETED',
        updated_at__date=today
    ).select_related('vehicle__owner')

    for order in completed_today_orders:
        customer = order.vehicle.owner
        subject = "Dziękujemy za wizytę w DetailFlow! Mamy dla Ciebie prezent"
        message = (
            f"Dzień dobry {customer.first_name},\n\n"
            f"Dziękujemy za zaufanie i powierzenie nam swojego {order.vehicle.make} {order.vehicle.model}.\n"
            f"W ramach podziękowania przygotowaliśmy kod rabatowy -10% na kolejną wizytę: DETAIL10\n\n"
            f"Do zobaczenia!\nZespół DetailFlow"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email="studio@detailflow.pl",
            recipient_list=[customer.email],
            fail_silently=True,
        )