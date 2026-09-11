from django.contrib import admin
from .models import (
    Customer,
    Vehicle,
    ServiceOrder,
    ChemicalProduct,
    PaintInspection,
    CoatingCertificate,
    DamagePoint,
    CarBlueprint,
    MaterialUsage,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email')
    search_fields = ('last_name', 'phone', 'email')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'license_plate', 'body_type', 'owner')
    search_fields = ('make', 'model', 'license_plate', 'vin')
    list_filter = ('body_type',)


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'vehicle', 'service_name', 'status',
        'price_total', 'scheduled_start', 'requires_paint_inspection',
        'requires_coating_certificate',
    )
    list_filter = ('status', 'requires_paint_inspection', 'requires_coating_certificate')


@admin.register(ChemicalProduct)
class ChemicalProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'current_stock', 'unit', 'cost_per_unit')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'category')


@admin.register(PaintInspection)
class PaintInspectionAdmin(admin.ModelAdmin):
    list_display = ('order', 'inspected_at')


@admin.register(CoatingCertificate)
class CoatingCertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'coating_product', 'warranty_months', 'issued_at')


@admin.register(DamagePoint)
class DamagePointAdmin(admin.ModelAdmin):
    list_display = ('order', 'car_view', 'damage_type', 'x_pos', 'y_pos')
    list_filter = ('car_view', 'damage_type')


@admin.register(CarBlueprint)
class CarBlueprintAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'created_at')
    search_fields = ('make', 'model')


@admin.register(MaterialUsage)
class MaterialUsageAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity_used', 'unit_cost_snapshot', 'created_at')
    list_filter = ('product',)
