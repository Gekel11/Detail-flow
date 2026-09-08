from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ServiceOrder
from .forms import ServiceOrderForm
from .tasks import send_vehicle_ready_notification

def dashboard_view(request):
    """Widok pulpitu - lista zleceń i statystyki warsztatu"""
    orders = ServiceOrder.objects.select_related('vehicle__owner').order_by('-created_at')
    
    context = {
        'orders': orders,
        'total_count': orders.count(),
        'in_progress_count': orders.filter(status='IN_PROGRESS').count(),
        'ready_count': orders.filter(status='READY').count(),
    }
    return render(request, 'workshop/dashboard.html', context)

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
