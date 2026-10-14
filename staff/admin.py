from django.contrib import admin

from .models import Department, Doctor


class DoctorInline(admin.TabularInline):
    model = Doctor
    fields = ["user", "specialization", "license_number", "is_available", "is_active"]
    extra = 0
    show_change_link = True


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "created_at"]
    search_fields = ["name", "location"]
    inlines = [DoctorInline]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["__str__", "department", "specialization", "license_number", "consultation_fee", "is_available", "is_active"]
    list_filter = ["department", "is_available", "is_active"]
    search_fields = ["user__first_name", "user__last_name", "license_number", "specialization"]
    list_select_related = ["user", "department"]
