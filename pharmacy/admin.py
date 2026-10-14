from django.contrib import admin

from .models import Medicine, Prescription, PrescriptionItem


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["name", "generic_name", "category", "unit_price", "stock_quantity", "reorder_level", "expiry_date"]
    list_filter = ["category"]
    search_fields = ["name", "generic_name"]


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0
    autocomplete_fields = ["medicine"]


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "medical_record", "status", "issued_at", "dispensed_at", "dispensed_by"]
    list_filter = ["status"]
    search_fields = ["medical_record__appointment__patient__first_name", "medical_record__appointment__patient__last_name"]
    list_select_related = ["medical_record__appointment__patient", "dispensed_by"]
    inlines = [PrescriptionItemInline]
