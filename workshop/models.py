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
        ('PENDING', 'W kolejce'),
        ('IN_PROGRESS', 'Rozpoczęte'),
        ('READY', 'Gotowe do wydania'),
        ('COMPLETED', 'Wydane'),
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


class CoatingCertificate(models.Model):
    order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='coating_certificate',
        verbose_name="Zlecenie detailingowe"
    )

    coating_product = models.CharField(max_length=120, default="Ceramic Base 9H + Top Coat",
                                       verbose_name="Produkt powłoki")
    coating_layers = models.PositiveSmallIntegerField(default=2, verbose_name="Liczba warstw")
    warranty_months = models.PositiveSmallIntegerField(default=36, verbose_name="Gwarancja (miesiące)")
    curing_time_hours = models.PositiveSmallIntegerField(default=24, verbose_name="Czas utwardzania (h)")

    # Pomiary grubości lakieru przed polerowaniem (µm)
    thickness_hood = models.CharField(max_length=30, default="110-130", verbose_name="Maska (µm)")
    thickness_roof = models.CharField(max_length=30, default="100-120", verbose_name="Dach (µm)")
    thickness_trunk = models.CharField(max_length=30, default="105-125", verbose_name="Klapa bagażnika (µm)")
    thickness_doors_left = models.CharField(max_length=30, default="95-115", verbose_name="Drzwi lewe (µm)")
    thickness_doors_right = models.CharField(max_length=30, default="95-115", verbose_name="Drzwi prawe (µm)")
    thickness_fenders = models.CharField(max_length=30, default="100-120", verbose_name="Błotniki (µm)")

    maintenance_guide = models.TextField(
        verbose_name="Zalecenia serwisowe",
        default=(
            "1. Mycie wyłącznie metodą na dwa wiadra z szamponem o neutralnym pH.\n"
            "2. Bezwzględny zakaz korzystania z myjni szczotkowych i agresywnej chemii bezdotykowej.\n"
            "3. Pierwsze mycie ręczne możliwe po minimum 14 dniach od aplikacji powłoki.\n"
            "4. Wymagany przegląd powłoki oraz dekontaminacja lakieru co 6 miesięcy lub 10 000 km."
        )
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Data wystawienia")

    def __str__(self):
        return f"Certyfikat #{self.id} (Zlecenie #{self.order.id})"

