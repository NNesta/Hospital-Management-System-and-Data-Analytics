from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["patient_code", "full_name", "gender", "date_of_birth", "phone", "district", "insurance_provider", "created_at"]
    list_filter = ["gender", "blood_group", "district", "insurance_provider"]
    search_fields = ["patient_code", "first_name", "last_name", "phone", "national_id"]
    readonly_fields = ["patient_code", "created_at", "updated_at"]
    date_hierarchy = "created_at"
