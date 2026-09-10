from django import forms
from .models import Customer, Vehicle, ServiceOrder, PaintInspection, CoatingCertificate

INPUT_STYLE = "w-full bg-stone-950 border border-stone-800 focus:border-amber-accent focus:ring-0 text-white font-mono text-xs px-3 py-2 outline-none transition"
CHECKBOX_STYLE = "w-4 h-4 accent-amber-accent bg-stone-900 border-stone-700 rounded cursor-pointer"

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Imię'}),
            'last_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Nazwisko'}),
            'email': forms.EmailInput(attrs={'class': INPUT_STYLE, 'placeholder': 'kontakt@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': '+48 000 000 000'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['owner', 'make', 'model', 'body_type', 'license_plate', 'paint_code', 'vin']
        widgets = {
            'owner': forms.Select(attrs={'class': INPUT_STYLE}),
            'make': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. BMW'}),
            'model': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. Seria 3'}),
            'body_type': forms.Select(attrs={'class': INPUT_STYLE}),
            'license_plate': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. RZ 12345'}),
            'paint_code': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. C31 Portimao Blue'}),
            'vin': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': '17 znaków'}),
        }

class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = [
            'vehicle', 'service_name', 'description', 
            'requires_paint_inspection', 'requires_coating_certificate',
            'price_total', 'deposit_paid', 'scheduled_start'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': INPUT_STYLE}),
            'service_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. Korekta 2-etap + Powłoka Ceramiczna'}),
            'description': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 3, 'placeholder': 'Uwagi techniczne...'}),
            'requires_paint_inspection': forms.CheckboxInput(attrs={'class': CHECKBOX_STYLE}),
            'requires_coating_certificate': forms.CheckboxInput(attrs={'class': CHECKBOX_STYLE}),
            'price_total': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00'}),
            'deposit_paid': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': INPUT_STYLE, 'type': 'datetime-local'}),
        }

class PaintInspectionForm(forms.ModelForm):
    class Meta:
        model = PaintInspection
        fields = [
            'thickness_hood', 'thickness_roof', 'thickness_trunk',
            'thickness_bumper_front', 'thickness_bumper_rear',
            'thickness_doors_fl', 'thickness_doors_fr',
            'thickness_doors_rl', 'thickness_doors_rr',
            'thickness_fenders_front', 'thickness_fenders_rear',
            'notes'
        ]
        widgets = {
            'thickness_hood': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 110-130'}),
            'thickness_roof': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120'}),
            'thickness_trunk': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 105-125'}),
            'thickness_bumper_front': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'N/D lub np. 90-110'}),
            'thickness_bumper_rear': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'N/D lub np. 90-110'}),
            'thickness_doors_fl': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120'}),
            'thickness_doors_fr': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120'}),
            'thickness_doors_rl': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120 lub N/D'}),
            'thickness_doors_rr': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120 lub N/D'}),
            'thickness_fenders_front': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 95-115'}),
            'thickness_fenders_rear': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'np. 100-120'}),
            'notes': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 2, 'placeholder': 'Uwagi do stanu lakieru...'}),
        }

class CoatingCertificateForm(forms.ModelForm):
    class Meta:
        model = CoatingCertificate
        fields = ['coating_product', 'coating_layers', 'warranty_months', 'curing_time_hours', 'maintenance_guide']
        widgets = {
            'coating_product': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'coating_layers': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'warranty_months': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'curing_time_hours': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'maintenance_guide': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 4}),
        }
