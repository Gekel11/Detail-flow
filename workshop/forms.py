from django import forms
from .models import ServiceOrder, Customer, Vehicle

class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ['vehicle', 'service_name', 'description', 'status', 'price_total', 'deposit_paid', 'scheduled_start']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-input'}),
            'service_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'np. Korekta 2-etapowa + Ceramika 5-letnia'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Uwagi, stan lakieru, zarysowania...'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'price_total': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'deposit_paid': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }