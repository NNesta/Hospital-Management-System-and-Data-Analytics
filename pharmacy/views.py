from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ProtectedDeleteMixin, RoleRequiredMixin, SearchMixin, StatusGuardMixin, role_required
from accounts.models import Role
from appointments.models import MedicalRecord

from .forms import MedicineForm, PrescriptionForm, PrescriptionItemFormSet
from .models import Medicine, Prescription
from .services import DispenseError, dispense_prescription

# --- Medicines -------------------------------------------------------------------------


class MedicineListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.PHARMACIST, Role.DOCTOR]
    model = Medicine
    paginate_by = 10
    search_fields = ["name", "generic_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)
        if self.request.GET.get("stock") == "low":
            queryset = queryset.filter(stock_quantity__lte=F("reorder_level"))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Medicine.Category.choices
        context["selected_category"] = self.request.GET.get("category", "")
        context["low_only"] = self.request.GET.get("stock") == "low"
        context["low_stock_count"] = Medicine.objects.filter(stock_quantity__lte=F("reorder_level")).count()
        return context


class MedicineDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.PHARMACIST, Role.DOCTOR]
    model = Medicine

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_items"] = (
            self.object.prescription_items.select_related(
                "prescription__medical_record__appointment__patient",
                "prescription__medical_record__appointment__doctor__user",
            )
            .order_by("-prescription__issued_at")[:10]
        )
        return context


class MedicineCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN, Role.PHARMACIST]
    model = Medicine
    form_class = MedicineForm
    success_message = "Medicine %(name)s was added."


class MedicineUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN, Role.PHARMACIST]
    model = Medicine
    form_class = MedicineForm
    success_message = "Medicine %(name)s was updated."


class MedicineDeleteView(RoleRequiredMixin, ProtectedDeleteMixin, DeleteView):
    """Only medicines that were never prescribed or invoiced can be deleted."""

    allowed_roles = [Role.ADMIN, Role.PHARMACIST]
    model = Medicine
    success_url = reverse_lazy("pharmacy:medicine_list")
    protected_message = "This medicine has already been prescribed or billed, so it cannot be deleted."


# --- Prescriptions -----------------------------------------------------------------------


class PrescriptionScopeMixin:
    """Doctors see the prescriptions they wrote; pharmacists and admins see all."""

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "medical_record__appointment__patient",
                "medical_record__appointment__doctor__user",
                "dispensed_by",
            )
        )
        if self.request.user.role == Role.DOCTOR:
            queryset = queryset.filter(medical_record__appointment__doctor__user=self.request.user)
        return queryset


class PrescriptionListView(RoleRequiredMixin, PrescriptionScopeMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.DOCTOR, Role.PHARMACIST]
    model = Prescription
    paginate_by = 10
    search_fields = [
        "medical_record__appointment__patient__first_name",
        "medical_record__appointment__patient__last_name",
        "medical_record__appointment__patient__patient_code",
        "medical_record__diagnosis",
    ]

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("items")
        status = self.request.GET.get("status")
        if status in Prescription.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Prescription.Status.choices
        context["selected_status"] = self.request.GET.get("status", "")
        return context


class PrescriptionDetailView(RoleRequiredMixin, PrescriptionScopeMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.DOCTOR, Role.PHARMACIST]
    model = Prescription

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = list(self.object.items.select_related("medicine"))
        context["items"] = items
        context["can_dispense"] = self.object.is_pending and all(
            item.medicine.stock_quantity >= item.quantity for item in items
        )
        return context


class PrescriptionFormsetMixin:
    """Save a Prescription and its item formset together, in one transaction."""

    def get_formset(self):
        instance = self.object if self.object else Prescription()
        return PrescriptionItemFormSet(self.request.POST or None, instance=instance, prefix="items")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("formset", self.get_formset())
        context["record"] = self.get_record()
        return context

    def form_valid(self, form):
        formset = PrescriptionItemFormSet(self.request.POST, instance=form.instance, prefix="items")
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, self.success_text)
        return redirect(self.object)

    def form_invalid(self, form):
        formset = PrescriptionItemFormSet(self.request.POST, instance=form.instance, prefix="items")
        formset.is_valid()  # populate row errors too
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class PrescriptionCreateView(RoleRequiredMixin, PrescriptionFormsetMixin, CreateView):
    """/pharmacy/prescriptions/new/<record_pk>/ - doctor prescribes for own consultation."""

    allowed_roles = [Role.DOCTOR]
    model = Prescription
    form_class = PrescriptionForm
    success_text = "Prescription sent to the pharmacy."

    def get_record(self):
        if not hasattr(self, "_record"):
            self._record = get_object_or_404(
                MedicalRecord.objects.select_related("appointment__patient", "appointment__doctor__user"),
                pk=self.kwargs["record_pk"],
                appointment__doctor__user=self.request.user,
            )
        return self._record

    def form_valid(self, form):
        form.instance.medical_record = self.get_record()
        return super().form_valid(form)


class PrescriptionUpdateView(RoleRequiredMixin, StatusGuardMixin, PrescriptionFormsetMixin, UpdateView):
    allowed_roles = [Role.DOCTOR]
    model = Prescription
    form_class = PrescriptionForm
    success_text = "Prescription updated."
    locked_message = "Dispensed prescriptions cannot be changed."

    def get_queryset(self):
        return super().get_queryset().filter(medical_record__appointment__doctor__user=self.request.user)

    def is_editable(self, obj):
        return obj.is_pending

    def get_record(self):
        return self.object.medical_record


class PrescriptionDeleteView(RoleRequiredMixin, StatusGuardMixin, DeleteView):
    allowed_roles = [Role.DOCTOR]
    model = Prescription
    success_url = reverse_lazy("pharmacy:prescription_list")
    locked_message = "Dispensed prescriptions cannot be deleted."

    def get_queryset(self):
        return super().get_queryset().filter(medical_record__appointment__doctor__user=self.request.user)

    def is_editable(self, obj):
        return obj.is_pending

    def form_valid(self, form):
        messages.success(self.request, f"{self.object.code} was deleted.")
        return super().form_valid(form)


@require_POST
@role_required(Role.PHARMACIST)
def prescription_dispense(request, pk):
    """Deduct stock and mark the prescription Dispensed (atomic, see services.py)."""
    prescription = get_object_or_404(Prescription, pk=pk)
    try:
        dispense_prescription(prescription, request.user)
    except DispenseError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"{prescription.code} dispensed. Stock levels were updated.")
        low = Medicine.objects.filter(
            prescription_items__prescription=prescription, stock_quantity__lte=F("reorder_level")
        )
        for medicine in low:
            messages.warning(request, f"Low stock: {medicine.name} has {medicine.stock_quantity} left.")
    return redirect(prescription)
