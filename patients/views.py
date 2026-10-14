from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ProtectedDeleteMixin, RoleRequiredMixin, SearchMixin
from accounts.models import Role

from .forms import PatientForm
from .models import DISTRICT_CHOICES, Patient


class PatientScopeMixin:
    """Doctors only see patients they have an appointment with."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == Role.DOCTOR:
            queryset = queryset.filter(appointments__doctor__user=user).distinct()
        return queryset


class PatientListView(RoleRequiredMixin, PatientScopeMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST, Role.DOCTOR, Role.ACCOUNTANT]
    model = Patient
    paginate_by = 10
    search_fields = ["patient_code", "first_name", "last_name", "phone", "national_id", "insurance_number"]

    def get_queryset(self):
        queryset = super().get_queryset()
        district = self.request.GET.get("district")
        if district:
            queryset = queryset.filter(district=district)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["district_choices"] = DISTRICT_CHOICES
        context["selected_district"] = self.request.GET.get("district", "")
        return context


class PatientDetailView(RoleRequiredMixin, PatientScopeMixin, DetailView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST, Role.DOCTOR, Role.ACCOUNTANT]
    model = Patient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        user = self.request.user
        appointments = patient.appointments.select_related("doctor__user", "doctor__department")
        context["appointments"] = appointments.order_by("-appointment_date", "-appointment_time")
        if user.role in (Role.ADMIN, Role.DOCTOR):
            context["records"] = (
                patient.appointments.filter(medical_record__isnull=False)
                .select_related("medical_record", "doctor__user")
                .order_by("-appointment_date")
            )
        if user.role in (Role.ADMIN, Role.RECEPTIONIST, Role.ACCOUNTANT):
            context["invoices"] = patient.invoices.prefetch_related("items", "payments").order_by(
                "-issue_date", "-pk"
            )
        return context


class PatientCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST]
    model = Patient
    form_class = PatientForm
    success_message = "Patient %(first_name)s %(last_name)s was registered."

    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        return super().form_valid(form)


class PatientUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN, Role.RECEPTIONIST]
    model = Patient
    form_class = PatientForm
    success_message = "Patient %(first_name)s %(last_name)s was updated."


class PatientDeleteView(RoleRequiredMixin, ProtectedDeleteMixin, DeleteView):
    allowed_roles = [Role.ADMIN]
    model = Patient
    success_url = reverse_lazy("patients:list")
    protected_message = "This patient has appointments or invoices, so the record is kept for history."
