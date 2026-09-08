from django.db import models

class Customer(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Imię")
    last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
    email = models.EmailField(verbose_name="Adres e-mail")
    phone = models.CharField(max_length=20, verbose_name="Numer telefonu")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

class Vehicle(models.Model):
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50, verbose_name="Marka")
    model = models.CharField(max_length=50, verbose_name="Model")
    vin = models.CharField(max_length=17, blank=True, null=True, verbose_name="Numer VIN")
    license_plate = models.CharField(max_length=15, verbose_name="Numer rejestracyjny")
    paint_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kod lakieru")

    def __str__(self):
        return f"{self.make} {self.model} [{self.license_plate}]"

class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Oczekuje na przyjęcie'),
        ('IN_PROGRESS', 'W trakcie prac'),
        ('READY', 'Gotowy do odbioru'),
        ('COMPLETED', 'Zakończone i wydane'),
        ('CANCELLED', 'Anulowane'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='orders')
    service_name = models.CharField(max_length=200, verbose_name="Nazwa usługi / pakietu")
    description = models.TextField(blank=True, verbose_name="Zakres prac / uwagi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    price_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota łączna (PLN)")
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Wpłacony zadatek (PLN)")
    scheduled_start = models.DateTimeField(verbose_name="Termin rozpoczęcia")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Faktyczne zakończenie")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zlecenie #{self.id} - {self.vehicle} ({self.get_status_display()})"