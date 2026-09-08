from django.contrib import admin
from .models import Customer, Vehicle, ServiceOrder

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email')
    search_fields = ('last_name', 'phone', 'email')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'license_plate', 'owner')
    search_fields = ('make', 'model', 'license_plate', 'vin')

@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'service_name', 'status', 'price_total', 'scheduled_start')
    list_filter = ('status', 'scheduled_start')