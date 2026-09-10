from django.db import models
from django.utils import timezone


class Customer(models.Model):
    first_name = models.CharField(max_length=64, verbose_name="Imię")
    last_name = models.CharField(max_length=64, verbose_name="Nazwisko")
    email = models.EmailField(verbose_name="Adres e-mail")
    phone = models.CharField(max_length=20, verbose_name="Numer telefonu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"


class Vehicle(models.Model):
    BODY_TYPES = [
        ('SEDAN', 'Sedan / Limuzyna'),
        ('COUPE', 'Coupe / Hatchback 3D'),
        ('SUV', 'SUV / Kombi / Crossover'),
    ]

    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles', verbose_name="Właściciel")
    make = models.CharField(max_length=64, verbose_name="Marka")
    model = models.CharField(max_length=64, verbose_name="Model")
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, default='SEDAN', verbose_name="Typ nadwozia")
    license_plate = models.CharField(max_length=15, unique=True, verbose_name="Numer rejestracyjny")
    paint_code = models.CharField(max_length=64, blank=True, null=True, verbose_name="Kod lakieru")
    vin = models.CharField(max_length=17, blank=True, null=True, verbose_name="Numer VIN")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Data utworzenia")

    def __str__(self):
        return f"{self.make} {self.model} [{self.license_plate}] ({self.get_body_type_display()})"


class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'W kolejce'),
        ('IN_PROGRESS', 'Rozpoczęte'),
        ('READY', 'Gotowe do wydania'),
        ('COMPLETED', 'Wydane'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='orders', verbose_name="Pojazd")
    service_name = models.CharField(max_length=128, verbose_name="Pakiet usług")
    description = models.TextField(blank=True, null=True, verbose_name="Opis / Uwagi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    price_total = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cena całkowita (PLN)")
    deposit_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, blank=True, null=True,
                                       verbose_name="Zadatek (PLN)")
    scheduled_start = models.DateTimeField(default=timezone.now, verbose_name="Termin wjazdu na halę")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Data wydania pojazdu")

    # Flagi sterujące logiką biznesową
    requires_paint_inspection = models.BooleanField(
        default=True,
        verbose_name="Wymaga inspekcji i pomiaru powłoki lakierniczej (np. Korekta / One-Step)"
    )
    requires_coating_certificate = models.BooleanField(
        default=True,
        verbose_name="Obejmuje aplikację powłoki ceramicznej / certyfikat"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    def __str__(self):
        return f"Zlecenie #{self.id} - {self.vehicle.make} {self.vehicle.model} [{self.vehicle.license_plate}] ({self.get_status_display()})"


class PaintInspection(models.Model):
    """Niezależny protokół pomiaru mikronowego lakieru przed ingerencją polerską"""
    order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='paint_inspection',
        verbose_name="Zlecenie"
    )
    thickness_hood = models.CharField(max_length=30, default="110-130", verbose_name="Maska silnika")
    thickness_roof = models.CharField(max_length=30, default="100-120", verbose_name="Dach")
    thickness_trunk = models.CharField(max_length=30, default="105-125", verbose_name="Klapa bagażnika")
    thickness_bumper_front = models.CharField(max_length=30, default="N/D", verbose_name="Zderzak przedni")
    thickness_bumper_rear = models.CharField(max_length=30, default="N/D", verbose_name="Zderzak tylny")
    thickness_doors_fl = models.CharField(max_length=30, default="100-120", verbose_name="Drzwi przednie lewe")
    thickness_doors_rl = models.CharField(max_length=30, default="100-120", verbose_name="Drzwi tylne lewe")
    thickness_doors_fr = models.CharField(max_length=30, default="100-120", verbose_name="Drzwi przednie prawe")
    thickness_doors_rr = models.CharField(max_length=30, default="100-120", verbose_name="Drzwi tylne prawe")
    thickness_fenders_front = models.CharField(max_length=30, default="95-115", verbose_name="Błotniki przednie (L/P)")
    thickness_fenders_rear = models.CharField(max_length=30, default="110-130",
                                              verbose_name="Błotniki tylne / słupki C")
    notes = models.TextField(blank=True, null=True, verbose_name="Uwagi do stanu powłoki lakierniczej")
    inspected_at = models.DateTimeField(auto_now_add=True, verbose_name="Data pomiaru")

    def __str__(self):
        return f"Inspekcja lakieru dla Zlecenia #{self.order_id}"


class CoatingCertificate(models.Model):
    """Certyfikat powłoki ceramicznej i warunki gwarancji"""
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
    maintenance_guide = models.TextField(
        verbose_name="Zalecenia serwisowe",
        default=(
            "1. Mycie wyłącznie metodą na dwa wiadra z szamponem o neutralnym pH.\n"
            "2. Bezwzględny zakaz korzystania z myjni automatycznych i agresywnej chemii bezdotykowej.\n"
            "3. Pierwsze mycie ręczne możliwe po minimum 14 dniach od aplikacji powłoki.\n"
            "4. Wymagany przegląd powłoki oraz dekontaminacja lakieru co 6 miesięcy lub 10 000 km."
        )
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Data wystawienia")

    def __str__(self):
        return f"Certyfikat #{self.id} (Zlecenie #{self.order.id})"

class DamagePoint(models.Model):
    DAMAGE_TYPES = [
        ('CHIP', 'Odprysk od kamienia'),
        ('SCRATCH', 'Głęboka rysa (do podkładu)'),
        ('DENT', 'Wgniecenie / wgniotka'),
        ('REPAINT', 'Ślad powtórnego lakieru / szpachla'),
        ('OTHER', 'Inna wada powłoki'),
    ]

    VIEW_CHOICES = [
        ('TOP', 'Rzut z góry'),
        ('LEFT', 'Profil lewy'),
        ('RIGHT', 'Profil prawy'),
        ('FRONT', 'Przód pojazdu'),
        ('REAR', 'Tył pojazdu'),
    ]

    order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='damage_points',
        verbose_name="Zlecenie"
    )
    car_view = models.CharField(max_length=10, choices=VIEW_CHOICES, default='TOP', verbose_name="Rzut / Perspektywa")
    x_pos = models.FloatField(verbose_name="Pozycja X (%)")
    y_pos = models.FloatField(verbose_name="Pozycja Y (%)")
    damage_type = models.CharField(
        max_length=20,
        choices=DAMAGE_TYPES,
        default='SCRATCH',
        verbose_name="Typ uszkodzenia"
    )
    note = models.CharField(max_length=128, blank=True, verbose_name="Krótka notatka")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    def __str__(self):
        return f"{self.get_car_view_display()}: {self.get_damage_type_display()} ({self.x_pos:.1f}%, {self.y_pos:.1f}%)"

class CarBlueprint(models.Model):
    """Zcache'owany kod wektorowy 5 rzutow auta wygenerowany przez AI"""
    make = models.CharField(max_length=64, verbose_name="Marka")
    model = models.CharField(max_length=64, verbose_name="Model")
    svg_code = models.TextField(verbose_name="Kod SVG rzutow")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('make', 'model')
        verbose_name = "Schemat techniczny auta"
        verbose_name_plural = "Schematy techniczne aut"

    def __str__(self):
        return f"Blueprint: {self.make} {self.model}"
