"""
Widoki MVT aplikacji workshop.

Zasady, których warto się trzymać:
1. Mutacje stanu (zmiana statusu, delete) = tylko POST, nigdy GET.
2. Nazwy pól w JSON/API = nazwy pól w modelu (car_view, nie view_angle).
3. Logika „czy starczy towaru” należy do serwisu/modelu, nie do szablonu.
4. Widoki chronimy @login_required — panel hali nie może być publiczny.
"""

import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .ai_services import get_or_generate_blueprint
from .forms import (
    CustomerForm,
    PaintInspectionForm,
    ServiceOrderForm,
    VehicleForm,
)
from .models import (
    ChemicalProduct,
    CoatingCertificate,
    DamagePoint,
    MaterialUsage,
    PaintInspection,
    ServiceOrder,
)
from .services import generate_coating_certificate_pdf
from .tasks import send_vehicle_ready_notification


@login_required
def dashboard_view(request):
    base_orders = ServiceOrder.objects.select_related('vehicle__owner')

    pending_count = base_orders.filter(status='PENDING').count()
    in_progress_count = base_orders.filter(status='IN_PROGRESS').count()
    ready_count = base_orders.filter(status='READY').count()
    completed_count = base_orders.filter(status='COMPLETED').count()
    cancelled_count = base_orders.filter(status='CANCELLED').count()

    current_filter = request.GET.get('status', 'default')

    if current_filter == 'PENDING':
        orders = base_orders.filter(status='PENDING')
    elif current_filter == 'IN_PROGRESS':
        orders = base_orders.filter(status='IN_PROGRESS')
    elif current_filter == 'READY':
        orders = base_orders.filter(status='READY')
    elif current_filter == 'COMPLETED':
        orders = base_orders.filter(status='COMPLETED')
    elif current_filter == 'CANCELLED':
        orders = base_orders.filter(status='CANCELLED')
    elif current_filter == 'ALL':
        orders = base_orders.all()
    else:
        current_filter = 'default'
        # Aktywna hala: wszystko poza wydanymi i anulowanymi
        orders = base_orders.exclude(status__in=['COMPLETED', 'CANCELLED'])

    orders = orders.order_by('-created_at')

    return render(request, 'workshop/dashboard.html', {
        'orders': orders,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'current_filter': current_filter,
    })


@login_required
def order_checkin_view(request, order_id):
    """Wjazd na halę: inspekcja lakieru wymagana tylko przy korekcie/polerowaniu."""
    order = get_object_or_404(
        ServiceOrder.objects.select_related('vehicle__owner'),
        id=order_id,
    )

    if not order.requires_paint_inspection:
        order.status = 'IN_PROGRESS'
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f"Zlecenie #{order.id}: pojazd wjechał na stanowisko (bez pomiaru lakieru).")
        return redirect('dashboard')

    inspection, _ = PaintInspection.objects.get_or_create(order=order)

    if request.method == 'POST':
        form = PaintInspectionForm(request.POST, instance=inspection)
        if form.is_valid():
            form.save()
            order.status = 'IN_PROGRESS'
            order.save(update_fields=['status', 'updated_at'])
            messages.success(
                request,
                f"Zlecenie #{order.id}: zapisano protokół lakieru. Pojazd wjechał na halę.",
            )
            return redirect('dashboard')
    else:
        form = PaintInspectionForm(instance=inspection)

    return render(request, 'workshop/order_checkin.html', {
        'order': order,
        'form': form,
        'inspection': inspection,
    })


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(
        ServiceOrder.objects.select_related('vehicle__owner').prefetch_related(
            'material_usages__product',
            'damage_points',
        ),
        id=order_id,
    )

    inspection = getattr(order, 'paint_inspection', None)
    certificate = getattr(order, 'coating_certificate', None)

    if order.requires_coating_certificate and certificate is None:
        certificate, _ = CoatingCertificate.objects.get_or_create(order=order)

    remaining_balance = order.price_total - (order.deposit_paid or 0)
    available_products = ChemicalProduct.objects.filter(current_stock__gt=0).order_by('name')

    return render(request, 'workshop/order_detail.html', {
        'order': order,
        'inspection': inspection,
        'cert': certificate,
        'remaining_balance': remaining_balance,
        'available_products': available_products,
    })


@login_required
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


@login_required
def order_create_view(request):
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(
                request,
                f"Pomyślnie utworzono zlecenie #{order.id} na pojazd {order.vehicle}!",
            )
            return redirect('dashboard')
    else:
        form = ServiceOrderForm()
    return render(request, 'workshop/order_form.html', {'form': form})


@login_required
def order_edit_view(request, order_id):
    """Edycja danych zlecenia (pakiet, ceny, flagi, termin) — bez zmiany statusu."""
    order = get_object_or_404(
        ServiceOrder.objects.select_related('vehicle__owner'),
        id=order_id,
    )

    if request.method == 'POST':
        form = ServiceOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Zapisano zmiany w zleceniu #{order.id}.")
            return redirect('order_detail', order_id=order.id)
    else:
        form = ServiceOrderForm(instance=order)

    return render(request, 'workshop/order_edit.html', {
        'form': form,
        'order': order,
    })


@login_required
@require_POST
def order_cancel_view(request, order_id):
    """Anulowanie zlecenia z karty szczegółów (tylko POST)."""
    order = get_object_or_404(ServiceOrder, id=order_id)

    if order.status in ('COMPLETED', 'CANCELLED'):
        messages.error(
            request,
            f"Zlecenia #{order.id} nie można anulować (status: {order.get_status_display()}).",
        )
        return redirect('order_detail', order_id=order.id)

    order.status = 'CANCELLED'
    order.completed_at = None
    order.save(update_fields=['status', 'completed_at', 'updated_at'])
    messages.success(request, f"Zlecenie #{order.id} zostało anulowane.")
    return redirect('order_detail', order_id=order.id)


@login_required
@require_POST
def order_update_status_view(request, order_id, new_status):
    """
    Zmiana statusu TYLKO przez POST.

    Dlaczego nie GET?
    - link w e-mailu / prefetch przeglądarki / bot mógłby przypadkiem zmienić status
    - GET ma być bezpieczny do odświeżenia (idempotentny odczyt)
    """
    order = get_object_or_404(ServiceOrder, id=order_id)
    valid_statuses = dict(ServiceOrder.STATUS_CHOICES)

    if new_status not in valid_statuses:
        messages.error(request, "Nieprawidłowy status.")
        return redirect('dashboard')

    old_status = order.status
    order.status = new_status

    if new_status == 'COMPLETED' and old_status != 'COMPLETED':
        order.completed_at = timezone.now()
    elif new_status != 'COMPLETED':
        # Jeśli cofamy z „wydane”, czyścimy datę wydania
        order.completed_at = None

    order.save(update_fields=['status', 'completed_at', 'updated_at'])

    if old_status != 'READY' and new_status == 'READY':
        send_vehicle_ready_notification.delay(order.id)
        messages.success(request, f"Zlecenie #{order.id}: auto gotowe. Wysłano maila do klienta.")
    elif old_status != 'COMPLETED' and new_status == 'COMPLETED':
        messages.success(request, f"Zlecenie #{order.id}: pojazd wydany klientowi.")
    elif new_status == 'CANCELLED':
        messages.success(request, f"Zlecenie #{order.id}: anulowane.")
    else:
        messages.success(request, f"Zlecenie #{order.id}: zmieniono status.")

    return redirect('dashboard')


@login_required
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


@login_required
def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(
                request,
                f"Dodano klienta: {customer.first_name} {customer.last_name}!",
            )
            return redirect('vehicle_create')
    else:
        form = CustomerForm()
    return render(request, 'workshop/customer_form.html', {'form': form})


@login_required
@require_POST
def mark_order_ready_view(request, order_id):
    """Skrót do READY — też tylko POST."""
    return order_update_status_view(request, order_id=order_id, new_status='READY')


@login_required
@require_POST
def add_damage_point_view(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    try:
        data = json.loads(request.body)
        # Akceptujemy car_view (właściwa nazwa). Stary view_angle zostaje jako fallback.
        car_view = data.get('car_view') or data.get('view_angle') or 'TOP'
        valid_views = {choice[0] for choice in DamagePoint.VIEW_CHOICES}
        if car_view not in valid_views:
            return JsonResponse({'status': 'error', 'message': 'Nieprawidłowy rzut auta.'}, status=400)

        damage_type = data.get('damage_type', 'SCRATCH')
        valid_types = {choice[0] for choice in DamagePoint.DAMAGE_TYPES}
        if damage_type not in valid_types:
            return JsonResponse({'status': 'error', 'message': 'Nieprawidłowy typ uszkodzenia.'}, status=400)

        point = DamagePoint.objects.create(
            order=order,
            car_view=car_view,
            x_pos=float(data.get('x', 0)),
            y_pos=float(data.get('y', 0)),
            damage_type=damage_type,
            note=(data.get('note') or '').strip(),
        )
        return JsonResponse({
            'status': 'ok',
            'id': point.id,
            'car_view': point.car_view,
            'view_label': point.get_car_view_display(),
            'x': point.x_pos,
            'y': point.y_pos,
            'type': point.damage_type,
            'type_label': point.get_damage_type_display(),
            'note': point.note,
        })
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@login_required
@require_POST
def delete_damage_point_view(request, point_id):
    point = get_object_or_404(DamagePoint, id=point_id)
    point.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def generate_ai_blueprint_view(request, order_id):
    order = get_object_or_404(ServiceOrder.objects.select_related('vehicle'), id=order_id)
    try:
        svg_code = get_or_generate_blueprint(order.vehicle.make, order.vehicle.model)
        return JsonResponse({'status': 'ok', 'svg_code': svg_code})
    except Exception as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@login_required
@require_POST
def add_material_usage_view(request, order_id):
    """
    Rejestracja zużycia materiału.
    Stock schodzi atomowo (transaction + select_for_update),
    żeby dwa równoległe requesty nie „zdjęły” więcej niż jest na półce.
    """
    order = get_object_or_404(ServiceOrder, id=order_id)
    product_id = request.POST.get('product_id')

    try:
        quantity = Decimal(request.POST.get('quantity', '0'))
    except (InvalidOperation, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Nieprawidłowa ilość.'}, status=400)

    if quantity <= 0:
        return JsonResponse({'status': 'error', 'message': 'Ilość musi być większa od zera.'}, status=400)

    try:
        with transaction.atomic():
            product = ChemicalProduct.objects.select_for_update().get(id=product_id)
            if product.current_stock < quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Za mało na stanie (dostępne: {product.current_stock}).',
                }, status=400)

            usage = MaterialUsage.objects.create(
                order=order,
                product=product,
                quantity_used=quantity,
            )
    except ChemicalProduct.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Nie znaleziono produktu.'}, status=404)

    return JsonResponse({
        'status': 'ok',
        'item': {
            'id': usage.id,
            'name': product.name,
            'quantity': float(usage.quantity_used),
            'unit': product.get_unit_display(),
            'unit_cost': float(usage.unit_cost_snapshot),
            'cost': float(usage.total_cost),
            'remaining_stock': float(product.current_stock),
        },
    })
