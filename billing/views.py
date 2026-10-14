from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin, SearchMixin, StatusGuardMixin, role_required
from accounts.models import Role
from appointments.models import Appointment

from .forms import InvoiceForm, InvoiceItemFormSet, PaymentForm
from .models import Invoice, Payment
from .services import InvoiceError, generate_invoice

FINANCE = [Role.ADMIN, Role.ACCOUNTANT]


# --- Invoices ----------------------------------------------------------------------------


class InvoiceListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.ACCOUNTANT, Role.RECEPTIONIST]
    model = Invoice
    paginate_by = 10
    search_fields = ["invoice_number", "patient__first_name", "patient__last_name", "patient__patient_code"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient").prefetch_related("items", "payments")
        status = self.request.GET.get("status")
        if status in Invoice.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Invoice.Status.choices
        context["selected_status"] = self.request.GET.get("status", "")
        return context


class InvoiceDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.ACCOUNTANT, Role.RECEPTIONIST]
    model = Invoice

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("patient", "appointment__doctor__user", "created_by")
            .prefetch_related("items__medicine", "payments__received_by")
        )


class InvoiceFormsetMixin:
    """Save an Invoice and its InvoiceItem rows in one transaction."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "formset" not in context:
            instance = self.object if self.object else Invoice()
            context["formset"] = InvoiceItemFormSet(instance=instance, prefix="items")
        return context

    def form_valid(self, form):
        formset = InvoiceItemFormSet(self.request.POST, instance=form.instance, prefix="items")
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        with transaction.atomic():
            if not form.instance.pk:
                form.instance.created_by = self.request.user
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            self.object.refresh_status()
        messages.success(self.request, self.success_text)
        return redirect(self.object)

    def form_invalid(self, form):
        formset = InvoiceItemFormSet(self.request.POST, instance=form.instance, prefix="items")
        formset.is_valid()
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class InvoiceCreateView(RoleRequiredMixin, InvoiceFormsetMixin, CreateView):
    allowed_roles = FINANCE
    model = Invoice
    form_class = InvoiceForm
    success_text = "Invoice created."

    def get_initial(self):
        initial = super().get_initial()
        patient = self.request.GET.get("patient")
        if patient and patient.isdigit():
            initial["patient"] = patient
        return initial


class InvoiceUpdateView(RoleRequiredMixin, StatusGuardMixin, InvoiceFormsetMixin, UpdateView):
    allowed_roles = FINANCE
    model = Invoice
    form_class = InvoiceForm
    success_text = "Invoice updated."
    locked_message = "Only unpaid invoices can be edited."

    def is_editable(self, obj):
        return obj.status == Invoice.Status.UNPAID


class InvoiceDeleteView(RoleRequiredMixin, StatusGuardMixin, DeleteView):
    allowed_roles = [Role.ADMIN]
    model = Invoice
    success_url = reverse_lazy("billing:invoice_list")
    locked_message = "Invoices with payments cannot be deleted."

    def is_editable(self, obj):
        return not obj.payments.exists()

    def form_valid(self, form):
        messages.success(self.request, f"{self.object} was deleted.")
        return super().form_valid(form)


@require_POST
@role_required(*FINANCE)
def invoice_generate(request, appointment_pk):
    """Build an invoice from the consultation fee and the dispensed medicines."""
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor__user", "doctor__department"), pk=appointment_pk
    )
    try:
        invoice = generate_invoice(appointment, request.user)
    except InvoiceError as error:
        messages.error(request, str(error))
        existing = Invoice.objects.filter(appointment=appointment).first()
        return redirect(existing or reverse("billing:pending"))
    messages.success(request, f"{invoice} generated for {appointment.patient.full_name}.")
    return redirect(invoice)


@role_required(Role.ADMIN, Role.ACCOUNTANT, Role.RECEPTIONIST)
def invoice_print(request, pk):
    """Printable invoice based on AdminLTE's invoice example page."""
    invoice = get_object_or_404(
        Invoice.objects.select_related("patient", "appointment__doctor__user", "appointment__doctor__department")
        .prefetch_related("items", "payments"),
        pk=pk,
    )
    return render(request, "billing/invoice_print.html", {"invoice": invoice})


class PendingBillingListView(RoleRequiredMixin, SearchMixin, ListView):
    """Completed visits that have no invoice yet: the accountant's work queue."""

    allowed_roles = FINANCE
    model = Appointment
    paginate_by = 10
    template_name = "billing/pending_list.html"
    search_fields = ["patient__first_name", "patient__last_name", "patient__patient_code"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status=Appointment.Status.COMPLETED, invoice__isnull=True)
            .select_related("patient", "doctor__user", "doctor__department")
            .order_by("-appointment_date", "-appointment_time")
        )


# --- Payments ----------------------------------------------------------------------------


class PaymentListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = FINANCE
    model = Payment
    paginate_by = 10
    search_fields = ["reference", "invoice__invoice_number", "invoice__patient__first_name", "invoice__patient__last_name"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("invoice__patient", "received_by")
        method = self.request.GET.get("method")
        if method in Payment.Method.values:
            queryset = queryset.filter(method=method)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["method_choices"] = Payment.Method.choices
        context["selected_method"] = self.request.GET.get("method", "")
        return context


class PaymentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = FINANCE
    model = Payment

    def get_queryset(self):
        return super().get_queryset().select_related("invoice__patient", "received_by")


class PaymentFormMixin:
    def get_invoice(self):
        raise NotImplementedError

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["invoice"] = self.get_invoice()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoice"] = self.get_invoice()
        return context

    def get_success_url(self):
        return self.get_invoice().get_absolute_url()


class PaymentCreateView(RoleRequiredMixin, PaymentFormMixin, SuccessMessageMixin, CreateView):
    """/billing/invoices/<pk>/payments/new/ - Payment.save() updates the invoice status."""

    allowed_roles = FINANCE
    model = Payment
    form_class = PaymentForm

    def get_invoice(self):
        if not hasattr(self, "_invoice"):
            self._invoice = get_object_or_404(Invoice.objects.prefetch_related("items", "payments"), pk=self.kwargs["pk"])
        return self._invoice

    def get(self, request, *args, **kwargs):
        if self.get_invoice().status == Invoice.Status.PAID:
            messages.info(request, "This invoice is already fully paid.")
            return redirect(self.get_invoice())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.invoice = self.get_invoice()
        form.instance.received_by = self.request.user
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return f"Payment of RWF {cleaned_data['amount']:,.0f} recorded. Invoice is now {self.object.invoice.get_status_display().lower()}."


class PaymentUpdateView(RoleRequiredMixin, PaymentFormMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN]
    model = Payment
    form_class = PaymentForm
    success_message = "Payment updated."

    def get_invoice(self):
        return Invoice.objects.prefetch_related("items", "payments").get(pk=self.get_object().invoice_id)


class PaymentDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [Role.ADMIN]
    model = Payment

    def get_success_url(self):
        return self.object.invoice.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "Payment deleted. The invoice status was recalculated.")
        return super().form_valid(form)
