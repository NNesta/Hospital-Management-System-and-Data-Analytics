from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "get_full_name", "role", "phone", "email", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "email", "phone"]
    fieldsets = DjangoUserAdmin.fieldsets + (("Hospital", {"fields": ("role", "phone")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Hospital", {"fields": ("first_name", "last_name", "role", "phone")}),
    )
