from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoices/new/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path("invoices/to-bill/", views.PendingBillingListView.as_view(), name="pending"),
    path("invoices/generate/<int:appointment_pk>/", views.invoice_generate, name="generate"),
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("invoices/<int:pk>/edit/", views.InvoiceUpdateView.as_view(), name="invoice_update"),
    path("invoices/<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="invoice_delete"),
    path("invoices/<int:pk>/print/", views.invoice_print, name="print"),
    path("invoices/<int:pk>/payments/new/", views.PaymentCreateView.as_view(), name="payment_create"),
    path("payments/", views.PaymentListView.as_view(), name="payment_list"),
    path("payments/<int:pk>/", views.PaymentDetailView.as_view(), name="payment_detail"),
    path("payments/<int:pk>/edit/", views.PaymentUpdateView.as_view(), name="payment_update"),
    path("payments/<int:pk>/delete/", views.PaymentDeleteView.as_view(), name="payment_delete"),
]
