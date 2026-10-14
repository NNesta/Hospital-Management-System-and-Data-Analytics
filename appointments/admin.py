from django.contrib import admin

from .models import Appointment, MedicalRecord


class MedicalRecordInline(admin.StackedInline):
    model = MedicalRecord
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["appointment_date", "appointment_time", "patient", "doctor", "status", "reason"]
    list_filter = ["status", "doctor__department", "appointment_date"]
    search_fields = ["patient__first_name", "patient__last_name", "patient__patient_code", "reason"]
    list_select_related = ["patient", "doctor__user"]
    date_hierarchy = "appointment_date"
    autocomplete_fields = ["patient"]
    inlines = [MedicalRecordInline]


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ["appointment", "diagnosis", "follow_up_date", "created_at"]
    search_fields = ["diagnosis", "appointment__patient__first_name", "appointment__patient__last_name"]
    list_select_related = ["appointment__patient", "appointment__doctor__user"]
