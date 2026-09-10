from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from .models import ServiceOrder, Customer, Vehicle, PaintInspection, CoatingCertificate
from .forms import ServiceOrderForm, VehicleForm, CustomerForm, PaintInspectionForm
from .tasks import send_vehicle_ready_notification
from .services import generate_coating_certificate_pdf


def dashboard_view(request):
    base_orders = ServiceOrder.objects.select_related('vehicle__owner')

    pending_count = base_orders.filter(status='PENDING').count()
    in_progress_count = base_orders.filter(status='IN_PROGRESS').count()
    ready_count = base_orders.filter(status='READY').count()
    completed_count = base_orders.filter(status='COMPLETED').count()

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
        current_filter = 'default'
        orders = base_orders.exclude(status='COMPLETED')

    orders = orders.order_by('-created_at')

    return render(request, 'workshop/dashboard.html', {
        'orders': orders,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'current_filter': current_filter,
    })


def order_checkin_view(request, order_id):
    """Wjazd na halę: inspekcja lakieru wymagana tylko przy korekcie/polerowaniu"""
    order = get_object_or_404(ServiceOrder.objects.select_related('vehicle__owner'), id=order_id)

    # Jeśli usługa NIE wymaga pomiaru (np. pranie tapicerki) -> bezpośredni wjazd
    if not order.requires_paint_inspection:
        order.status = 'IN_PROGRESS'
        order.save()
        messages.success(request, f"Zlecenie #{order.id}: Pojazd wjechał na stanowisko robocze.")
        return redirect('dashboard')

    # Wymaga inspekcji lakieru
    inspection, _ = PaintInspection.objects.get_or_create(order=order)

    if request.method == 'POST':
        form = PaintInspectionForm(request.POST, instance=inspection)
        if form.is_valid():
            form.save()
            order.status = 'IN_PROGRESS'
            order.save()
            messages.success(request, f"Zlecenie #{order.id}: Zapisano protokół lakieru. Pojazd wjechał na halę.")
            return redirect('dashboard')
    else:
        form = PaintInspectionForm(instance=inspection)

    return render(request, 'workshop/order_checkin.html', {
        'order': order,
        'form': form,
        'inspection': inspection,
    })

from .models import ChemicalProduct, MaterialUsage

def order_detail_view(request, order_id):
    order = get_object_or_404(
        ServiceOrder.objects.select_related('vehicle__owner').prefetch_related('material_usages__product', 'damage_points'),
        id=order_id
    )

    # Bezpieczne pobranie powiazanych obiektow
    inspection = getattr(order, 'paint_inspection', None)
    certificate = getattr(order, 'coating_certificate', None)

    # Jesli zlecenie wymaga certyfikatu, a jeszcze go nie ma, tworz go automatycznie
    if order.requires_coating_certificate and not certificate:
        certificate, _ = CoatingCertificate.objects.get_or_create(order=order)

    remaining_balance = order.price_total - (order.deposit_paid or 0)

    # Pobranie dostepnej chemii ze stanem wiekszym niz 0
    available_products = ChemicalProduct.objects.filter(current_stock__gt=0).order_by('name')

    return render(request, 'workshop/order_detail.html', {
        'order': order,
        'inspection': inspection,
        'cert': certificate,
        'remaining_balance': remaining_balance,
        'available_products': available_products,
    })


def download_certificate_pdf_view(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    if not order.requires_coating_certificate:
        messages.error(request, "To zlecenie nie obejmuje certyfikatu powłoki.")
        return redirect('order_detail', order_id=order.id)

    certificate, _ = CoatingCertificate.objects.get_or_create(order=order)
    pdf_bytes = generate_coating_certificate_pdf(certificate)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"Certyfikat_{order.vehicle.license_plate}_{order.id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def order_create_view(request):
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f"Pomyślnie utworzono zlecenie #{order.id} na pojazd {order.vehicle}!")
            return redirect('dashboard')
    else:
        form = ServiceOrderForm()
    return render(request, 'workshop/order_form.html', {'form': form})


def order_update_status_view(request, order_id, new_status):
    order = get_object_or_404(ServiceOrder, id=order_id)
    valid_statuses = dict(ServiceOrder.STATUS_CHOICES)

    if new_status in valid_statuses:
        old_status = order.status
        order.status = new_status
        order.save()

        if old_status != 'READY' and new_status == 'READY':
            send_vehicle_ready_notification.delay(order.id)
            messages.success(request, f"Zlecenie #{order.id}: auto gotowe. Wysłano maila do klienta.")
        elif old_status != 'COMPLETED' and new_status == 'COMPLETED':
            messages.success(request, f"Zlecenie #{order.id}: pojazd wydany klientowi.")
        else:
            messages.success(request, f"Zlecenie #{order.id}: zmieniono status.")
    return redirect('dashboard')


def vehicle_create_view(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f"Dodano pojazd {vehicle}!")
            return redirect('order_create')
    else:
        form = VehicleForm()
    return render(request, 'workshop/vehicle_form.html', {'form': form})


def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Dodano klienta: {customer.first_name} {customer.last_name}!")
            return redirect('vehicle_create')
    else:
        form = CustomerForm()
    return render(request, 'workshop/customer_form.html', {'form': form})

def mark_order_ready_view(request, order_id):
    """Skrót do oznaczenia zlecenia jako gotowe do odbioru."""
    return order_update_status_view(request, order_id=order_id, new_status='READY')

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import DamagePoint

@require_POST
def add_damage_point_view(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    try:
        data = json.loads(request.body)
        point = DamagePoint.objects.create(
            order=order,
            car_view=data.get('car_view', 'TOP'),
            x_pos=float(data.get('x', 0)),
            y_pos=float(data.get('y', 0)),
            damage_type=data.get('damage_type', 'SCRATCH'),
            note=data.get('note', '').strip(),
        )
        return JsonResponse({
            'status': 'ok',
            'id': point.id,
            'view': point.car_view,
            'view_label': point.get_car_view_display(),
            'x': point.x_pos,
            'y': point.y_pos,
            'type': point.damage_type,
            'type_label': point.get_damage_type_display(),
            'note': point.note,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def delete_damage_point_view(request, point_id):
    point = get_object_or_404(DamagePoint, id=point_id)
    point.delete()
    return JsonResponse({'status': 'ok'})

from .ai_services import get_or_generate_blueprint

@require_POST
def generate_ai_blueprint_view(request, order_id):
    order = get_object_or_404(ServiceOrder.objects.select_related('vehicle'), id=order_id)
    try:
        svg_code = get_or_generate_blueprint(order.vehicle.make, order.vehicle.model)
        return JsonResponse({'status': 'ok', 'svg_code': svg_code})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

from decimal import Decimal
from django.db.models import Sum, F
from django.views.decorators.http import require_POST
from .models import ChemicalProduct, MaterialUsage

@require_POST
def add_material_usage_view(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    product_id = request.POST.get('product_id')
    quantity = Decimal(request.POST.get('quantity', '0'))

    if quantity <= 0:
        return JsonResponse({'status': 'error', 'message': 'Ilość musi być większa od zera.'}, status=400)

    product = get_object_or_404(ChemicalProduct, id=product_id)
    usage = MaterialUsage.objects.create(
        order=order,
        product=product,
        quantity_used=quantity
    )

    return JsonResponse({
        'status': 'ok',
        'item': {
            'id': usage.id,
            'name': product.name,
            'quantity': float(usage.quantity_used),
            'unit': product.get_unit_display(),
            'cost': float(usage.total_cost)
        }
    })