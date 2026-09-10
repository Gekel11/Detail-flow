from django import forms
from .models import ServiceOrder, Vehicle, Customer

INPUT_STYLE = (
    "w-full bg-stone-950 border border-stone-800 text-stone-200 text-xs font-mono "
    "px-3.5 py-2.5 focus:border-amber-accent focus:ring-0 focus:outline-none placeholder-stone-600 rounded-none"
)

SELECT_STYLE = (
    "w-full bg-stone-950 border border-stone-800 text-stone-200 text-xs font-mono "
    "px-3.5 py-2.5 focus:border-amber-accent focus:ring-0 focus:outline-none rounded-none"
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. Jan'}),
            'last_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. Kowalski'}),
            'email': forms.EmailInput(attrs={'class': INPUT_STYLE, 'placeholder': 'klient@domena.pl'}),
            'phone': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': '+48 500 600 700'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['owner', 'make', 'model', 'license_plate', 'paint_code', 'vin']
        widgets = {
            'owner': forms.Select(attrs={'class': SELECT_STYLE}),
            'make': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. BMW'}),
            'model': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. M3 Competition'}),
            'license_plate': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'RZ 12345'}),
            'paint_code': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. C31 Portimao Blue'}),
            'vin': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'WBA... (opcjonalnie)'}),
        }

class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ['vehicle', 'service_name', 'description', 'status', 'price_total', 'deposit_paid', 'scheduled_start']
        widgets = {
            'vehicle': forms.Select(attrs={'class': SELECT_STYLE}),
            'service_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. Pełna korekta lakieru + Powłoka elastomerowa'}),
            'description': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 4, 'placeholder': 'Inspekcja grubości lakieru, zarysowania, stan tapicerki...'}),
            'status': forms.Select(attrs={'class': SELECT_STYLE}),
            'price_total': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00'}),
            'deposit_paid': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': INPUT_STYLE, 'type': 'datetime-local'}),
        }