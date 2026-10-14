from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import (
    ProtectedDeleteMixin,
    RoleRequiredMixin,
    SearchMixin,
    StatusGuardMixin,
    role_required,
)
from accounts.models import Role
from patients.models import Patient

from .forms import AppointmentFilterForm, AppointmentForm, MedicalRecordForm
from .models import Appointment, MedicalRecord


class DoctorScopeMixin:
    """Doctors only see their own appointments."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == Role.DOCTOR:
            queryset = queryset.filter(doctor__user=self.request.user)
        return queryset


# --- Appointments --------------------------------------------------------------------


class AppointmentListView(RoleRequiredMixin, DoctorScopeMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST, Role.DOCTOR]
    model = Appointment
    paginate_by = 10
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__patient_code",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "reason",
    ]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "doctor__user", "doctor__department")
        self.filter_form = AppointmentFilterForm(self.request.GET or None)
        return self.filter_form.filter(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class AppointmentDetailView(RoleRequiredMixin, DoctorScopeMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST, Role.DOCTOR]
    model = Appointment

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "doctor__user", "doctor__department", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.object
        record = getattr(appointment, "medical_record", None)
        context["record"] = record
        context["prescriptions"] = (
            record.prescriptions.prefetch_related("items__medicine") if record else []
        )
        context["invoice"] = getattr(appointment, "invoice", None)
        context["is_own"] = appointment.doctor.user_id == self.request.user.pk
        return context


class AppointmentCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST]
    model = Appointment
    form_class = AppointmentForm
    success_message = "Appointment booked."

    def get_initial(self):
        """Book from a patient's page: /appointments/new/?patient=<pk>."""
        initial = super().get_initial()
        patient_pk = self.request.GET.get("patient")
        if patient_pk and patient_pk.isdigit():
            initial["patient"] = get_object_or_404(Patient, pk=patient_pk)
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class AppointmentUpdateView(RoleRequiredMixin, StatusGuardMixin, SuccessMessageMixin, UpdateView):
    """Reschedule (only while the appointment is still Scheduled)."""

    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST]
    model = Appointment
    form_class = AppointmentForm
    success_message = "Appointment rescheduled."
    locked_message = "Only scheduled appointments can be rescheduled."

    def is_editable(self, obj):
        return obj.is_scheduled


@role_required(Role.DOCTOR)
def appointment_complete(request, pk):
    """Doctor writes the medical record; the appointment becomes Completed."""
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor__user"), pk=pk, doctor__user=request.user
    )
    if not appointment.is_scheduled:
        messages.error(request, "This appointment is not open for consultation.")
        return redirect(appointment)

    form = MedicalRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            record = form.save(commit=False)
            record.appointment = appointment
            record.save()
            appointment.status = Appointment.Status.COMPLETED
            appointment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Consultation saved. You can now write a prescription.")
        return redirect(appointment)

    history = (
        MedicalRecord.objects.filter(appointment__patient=appointment.patient)
        .select_related("appointment__doctor__user")
        .order_by("-created_at")[:5]
    )
    return render(
        request,
        "appointments/appointment_complete.html",
        {"appointment": appointment, "form": form, "history": history},
    )


@role_required(Role.ADMIN, Role.RECEPTIONIST)
def appointment_cancel(request, pk):
    """GET shows a confirmation page; POST cancels."""
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor__user"), pk=pk)
    if not appointment.is_scheduled:
        messages.error(request, "Only scheduled appointments can be cancelled.")
        return redirect(appointment)
    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Appointment cancelled.")
        return redirect(appointment)
    return render(request, "appointments/appointment_confirm_cancel.html", {"appointment": appointment})


@require_POST
@role_required(Role.ADMIN, Role.RECEPTIONIST)
def appointment_no_show(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.is_scheduled:
        appointment.status = Appointment.Status.NO_SHOW
        appointment.save(update_fields=["status", "updated_at"])
        messages.warning(request, "Appointment marked as no-show.")
    return redirect(appointment)


# --- Medical records -----------------------------------------------------------------


class RecordScopeMixin:
    """Doctors read the history of patients they treat; admins read everything."""

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("appointment__patient", "appointment__doctor__user", "appointment__doctor__department")
        )
        user = self.request.user
        if user.role == Role.DOCTOR:
            own_patients = Patient.objects.filter(appointments__doctor__user=user)
            queryset = queryset.filter(appointment__patient__in=own_patients).distinct()
        return queryset


class MedicalRecordListView(RoleRequiredMixin, RecordScopeMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.DOCTOR]
    model = MedicalRecord
    paginate_by = 10
    search_fields = [
        "diagnosis",
        "symptoms",
        "appointment__patient__first_name",
        "appointment__patient__last_name",
        "appointment__patient__patient_code",
    ]


class MedicalRecordDetailView(RoleRequiredMixin, RecordScopeMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.DOCTOR]
    model = MedicalRecord

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prescriptions"] = self.object.prescriptions.prefetch_related("items__medicine")
        context["is_author"] = self.object.appointment.doctor.user_id == self.request.user.pk
        return context


class MedicalRecordUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    """Only the doctor who wrote the record may edit it."""

    allowed_roles = [Role.DOCTOR]
    model = MedicalRecord
    form_class = MedicalRecordForm
    success_message = "Medical record updated."

    def get_queryset(self):
        return super().get_queryset().filter(appointment__doctor__user=self.request.user)


class MedicalRecordDeleteView(RoleRequiredMixin, ProtectedDeleteMixin, DeleteView):
    allowed_roles = [Role.ADMIN]
    model = MedicalRecord
    success_url = reverse_lazy("appointments:record_list")
    protected_message = "This record has prescriptions. Delete them first."
