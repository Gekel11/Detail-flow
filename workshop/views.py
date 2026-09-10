from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ServiceOrder
from .forms import ServiceOrderForm
from .tasks import send_vehicle_ready_notification
from .forms import ServiceOrderForm, VehicleForm

def dashboard_view(request):
    """Widok pulpitu z filtrowaniem i zliczaniem każdego statusu"""
    base_orders = ServiceOrder.objects.select_related('vehicle__owner')

    # Niezależne zliczanie dla górnych kafelków
    pending_count = base_orders.filter(status='PENDING').count()
    in_progress_count = base_orders.filter(status='IN_PROGRESS').count()
    ready_count = base_orders.filter(status='READY').count()
    completed_count = base_orders.filter(status='COMPLETED').count()

    # Odczyt parametru filtrowania z URL (?status=...)
    current_filter = request.GET.get('status', 'default')

    if current_filter == 'PENDING':
        orders = base_orders.filter(status='PENDING')
    elif current_filter == 'IN_PROGRESS':
        orders = base_orders.filter(status='IN_PROGRESS')
    elif current_filter == 'READY':
        orders = base_orders.filter(status='READY')
    elif current_filter == 'COMPLETED':
        orders = base_orders.filter(status='COMPLETED')
    elif current_filter == 'ALL':
        orders = base_orders.all()
    else:
        # DOMYŚLNIE: ukrywamy wydane (tylko bieżąca praca studia)
        current_filter = 'default'
        orders = base_orders.exclude(status='COMPLETED')

    orders = orders.order_by('-created_at')

    context = {
        'orders': orders,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'current_filter': current_filter,
    }
    return render(request, 'workshop/dashboard.html', context)


from django.http import HttpResponse
from .models import CoatingCertificate
from .services import generate_coating_certificate_pdf


def download_certificate_pdf_view(request, order_id):
    """Generuje i pobiera certyfikat powłoki dla danego zlecenia."""
    order = get_object_or_404(ServiceOrder, id=order_id)
    certificate, _ = CoatingCertificate.objects.get_or_create(order=order)

    pdf_bytes = generate_coating_certificate_pdf(certificate)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"Certyfikat_{order.vehicle.license_plate}_{order.id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def order_detail_view(request, order_id):
    """Panel techniczny zlecenia z kartą powłoki i pobieraniem PDF"""
    order = get_object_or_404(ServiceOrder.objects.select_related('vehicle__owner'), id=order_id)

    # Pobierz lub utwórz certyfikat dla tego zlecenia
    certificate, _ = CoatingCertificate.objects.get_or_create(order=order)

    remaining_balance = order.price_total - (order.deposit_paid or 0)

    context = {
        'order': order,
        'cert': certificate,
        'remaining_balance': remaining_balance,
    }
    return render(request, 'workshop/order_detail.html', context)



def order_create_view(request):
    """Widok formularza przyjęcia nowego pojazdu"""
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f"Pomyślnie utworzono zlecenie #{order.id} na pojazd {order.vehicle}!")
            return redirect('dashboard')
    else:
        form = ServiceOrderForm()

    return render(request, 'workshop/order_form.html', {'form': form})

def mark_order_ready_view(request, order_id):
    """Akcja oznaczenia jako gotowy do odbioru + asynchroniczny mail w Celery"""
    order = get_object_or_404(ServiceOrder, id=order_id)
    order.status = 'READY'
    order.save()

    # Wywołanie zadania Celery w tle
    send_vehicle_ready_notification.delay(order.id)

    messages.success(request, f"Zlecenie #{order.id} oznaczone jako GOTOWE. Wysłano maila do klienta!")
    return redirect('dashboard')

def vehicle_create_view(request):
    """Formularz dodawania nowego auta do bazy"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f"Dodano pojazd {vehicle} do kartoteki!")
            return redirect('order_create')
    else:
        form = VehicleForm()

    return render(request, 'workshop/vehicle_form.html', {'form': form})

from .forms import ServiceOrderForm, VehicleForm, CustomerForm

def customer_create_view(request):
    """Formularz dodawania nowego klienta"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Dodano klienta: {customer.first_name} {customer.last_name}!")
            return redirect('vehicle_create')
    else:
        form = CustomerForm()

    return render(request, 'workshop/customer_form.html', {'form': form})


def order_update_status_view(request, order_id, new_status):
    order = get_object_or_404(ServiceOrder, id=order_id)
    valid_statuses = dict(ServiceOrder.STATUS_CHOICES)

    if new_status in valid_statuses:
        old_status = order.status
        order.status = new_status
        order.save()

        # Przejście na "Gotowe do wydania" -> natychmiastowy mail z kwotą
        if old_status != 'READY' and new_status == 'READY':
            send_vehicle_ready_notification.delay(order.id)
            messages.success(request,
                             f"Zlecenie #{order.id}: auto gotowe do odbioru. Wysłano e-mail z podsumowaniem do klienta.")

        # Przejście na "Wydane" -> potwierdzenie odbioru
        elif old_status != 'COMPLETED' and new_status == 'COMPLETED':
            messages.success(request,
                             f"Zlecenie #{order.id}: pojazd wydany klientowi. Wieczorny e-mail z kodem rabatowym zostanie wysłany o 20:00.")
        else:
            messages.success(request, f"Zlecenie #{order.id}: zmieniono status na '{valid_statuses[new_status]}'.")
    else:
        messages.error(request, "Nieprawidłowy status zlecenia.")

    return redirect('dashboard')
