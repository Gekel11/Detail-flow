"""
Idempotentne dane startowe — uruchamiane automatycznie przy starcie kontenera web.

Login demo: demo / demo1234
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from workshop.models import ChemicalProduct, Customer, ServiceOrder, Vehicle


class Command(BaseCommand):
    help = "Tworzy konto demo i przykładowe dane (tylko gdy baza jest pusta)."

    def handle(self, *args, **options):
        User = get_user_model()
        demo, created = User.objects.get_or_create(
            username='demo',
            defaults={'is_staff': True, 'is_superuser': True},
        )
        demo.set_password('demo1234')
        demo.is_staff = True
        demo.is_superuser = True
        demo.save()

        if created:
            self.stdout.write(self.style.SUCCESS('Utworzono użytkownika demo / demo1234'))
        else:
            self.stdout.write('Konto demo / demo1234 — hasło zresetowane')

        if ServiceOrder.objects.exists():
            self.stdout.write('Zlecenia już istnieją — pomijam seed danych.')
            return

        anna = Customer.objects.create(
            first_name='Anna',
            last_name='Nowak',
            email='anna.nowak@example.com',
            phone='+48 600 100 200',
        )
        piotr = Customer.objects.create(
            first_name='Piotr',
            last_name='Kowalski',
            email='piotr.kowalski@example.com',
            phone='+48 512 333 444',
        )
        bmw = Vehicle.objects.create(
            owner=anna,
            make='BMW',
            model='M3 Competition',
            body_type='COUPE',
            license_plate='WA 1234A',
            paint_code='Sao Paulo Yellow',
        )
        porsche = Vehicle.objects.create(
            owner=piotr,
            make='Porsche',
            model='911 Carrera S',
            body_type='COUPE',
            license_plate='KR 9DETAL',
        )
        now = timezone.now()
        ServiceOrder.objects.create(
            vehicle=bmw,
            service_name='Korekta 2-etapowa + ceramika',
            status='PENDING',
            price_total=Decimal('4500.00'),
            deposit_paid=Decimal('1500.00'),
            scheduled_start=now,
            requires_paint_inspection=True,
            requires_coating_certificate=True,
        )
        ServiceOrder.objects.create(
            vehicle=porsche,
            service_name='Korekta + powłoka',
            status='IN_PROGRESS',
            price_total=Decimal('2500.00'),
            deposit_paid=Decimal('250.00'),
            scheduled_start=now,
            requires_paint_inspection=True,
            requires_coating_certificate=True,
        )
        ChemicalProduct.objects.create(
            name='Ceramic Coat 30ml',
            category='Powłoka',
            current_stock=Decimal('100.00'),
            unit='ML',
            cost_per_unit=Decimal('2.5000'),
        )
        self.stdout.write(self.style.SUCCESS('Dodano przykładowych klientów, auta i zlecenia.'))
