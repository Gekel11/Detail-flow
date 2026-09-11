"""
Podstawowe testy happy-path DetailFlow.

Uruchomienie w Dockerze:
  docker compose exec web python manage.py test workshop

Czego uczą te testy:
- kontrakt JSON (car_view),
- mutacje tylko POST,
- ustawianie completed_at,
- zejście stocku przy MaterialUsage,
- wymóg logowania.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from workshop.models import (
    ChemicalProduct,
    Customer,
    DamagePoint,
    MaterialUsage,
    ServiceOrder,
    Vehicle,
)


@override_settings(
    # Celery niech nie odpala prawdziwego brokera w testach
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class WorkshopFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='operator',
            password='test-pass-123',
        )
        self.client = Client()
        self.client.login(username='operator', password='test-pass-123')

        self.customer = Customer.objects.create(
            first_name='Anna',
            last_name='Nowak',
            email='anna@example.com',
            phone='600100200',
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.customer,
            make='BMW',
            model='M3',
            body_type='COUPE',
            license_plate='WA TEST01',
        )
        self.order = ServiceOrder.objects.create(
            vehicle=self.vehicle,
            service_name='Korekta + ceramika',
            status='IN_PROGRESS',
            price_total=Decimal('4500.00'),
            deposit_paid=Decimal('1000.00'),
            scheduled_start=timezone.now(),
            requires_paint_inspection=True,
            requires_coating_certificate=True,
        )
        self.product = ChemicalProduct.objects.create(
            name='Ceramic Coat 30ml',
            category='Powłoka',
            current_stock=Decimal('100.00'),
            unit='ML',
            cost_per_unit=Decimal('2.5000'),
        )

    def test_dashboard_requires_login(self):
        anon = Client()
        response = anon.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_status_change_rejects_get(self):
        url = reverse('order_update_status', args=[self.order.id, 'READY'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'IN_PROGRESS')

    def test_status_ready_and_completed_sets_completed_at(self):
        ready_url = reverse('order_update_status', args=[self.order.id, 'READY'])
        response = self.client.post(ready_url)
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'READY')
        self.assertIsNone(self.order.completed_at)

        completed_url = reverse('order_update_status', args=[self.order.id, 'COMPLETED'])
        self.client.post(completed_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'COMPLETED')
        self.assertIsNotNone(self.order.completed_at)

    def test_damage_point_uses_car_view_contract(self):
        url = reverse('order_damage_add', args=[self.order.id])
        payload = {
            'car_view': 'LEFT',
            'x': 12.5,
            'y': 40.0,
            'damage_type': 'CHIP',
            'note': 'rant drzwi',
        }
        response = self.client.post(
            url,
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['car_view'], 'LEFT')

        point = DamagePoint.objects.get(id=data['id'])
        self.assertEqual(point.car_view, 'LEFT')
        self.assertEqual(point.damage_type, 'CHIP')

    def test_material_usage_decrements_stock(self):
        url = reverse('order_add_material', args=[self.order.id])
        response = self.client.post(url, {'product_id': self.product.id, 'quantity': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal('70.00'))
        self.assertEqual(MaterialUsage.objects.count(), 1)

    def test_material_usage_rejects_overdraw(self):
        url = reverse('order_add_material', args=[self.order.id])
        response = self.client.post(url, {'product_id': self.product.id, 'quantity': '999'})
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal('100.00'))

    def test_order_edit_updates_fields(self):
        url = reverse('order_edit', args=[self.order.id])
        response = self.client.post(url, {
            'vehicle': self.vehicle.id,
            'service_name': 'Pakiet VIP',
            'description': 'Nowe uwagi',
            'requires_paint_inspection': 'on',
            'requires_coating_certificate': 'on',
            'price_total': '5000.00',
            'deposit_paid': '1500.00',
            'scheduled_start': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.service_name, 'Pakiet VIP')
        self.assertEqual(self.order.price_total, Decimal('5000.00'))

    def test_order_cancel_from_detail(self):
        url = reverse('order_cancel', args=[self.order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'CANCELLED')

    def test_order_cancel_blocked_when_completed(self):
        self.order.status = 'COMPLETED'
        self.order.completed_at = timezone.now()
        self.order.save(update_fields=['status', 'completed_at'])
        url = reverse('order_cancel', args=[self.order.id])
        self.client.post(url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'COMPLETED')
