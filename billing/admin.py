from django.contrib import admin

from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "patient", "issue_date", "due_date", "status"]
    list_filter = ["status", "issue_date"]
    search_fields = ["invoice_number", "patient__first_name", "patient__last_name", "patient__patient_code"]
    list_select_related = ["patient"]
    readonly_fields = ["invoice_number", "created_at"]
    date_hierarchy = "issue_date"
    inlines = [InvoiceItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice", "amount", "method", "reference", "paid_at", "received_by"]
    list_filter = ["method", "paid_at"]
    search_fields = ["reference", "invoice__invoice_number"]
    list_select_related = ["invoice", "received_by"]
    date_hierarchy = "paid_at"
