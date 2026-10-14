from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ProtectedDeleteMixin, RoleRequiredMixin, SearchMixin
from accounts.models import Role

from .forms import DepartmentForm, DoctorForm
from .models import Department, Doctor

ALL_ROLES = Role.values


# --- Departments ------------------------------------------------------------------


class DepartmentListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = ALL_ROLES
    model = Department
    paginate_by = 10
    search_fields = ["name", "location", "description"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                doctor_count=Count("doctors", filter=Q(doctors__is_active=True), distinct=True)
            )
            .order_by("name")  # GROUP BY queries ignore Meta.ordering
        )


class DepartmentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = ALL_ROLES
    model = Department

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doctors"] = self.object.doctors.select_related("user").order_by(
            "-is_active", "user__first_name"
        )
        return context


class DepartmentCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN]
    model = Department
    form_class = DepartmentForm
    success_message = "Department %(name)s was created."


class DepartmentUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN]
    model = Department
    form_class = DepartmentForm
    success_message = "Department %(name)s was updated."


class DepartmentDeleteView(RoleRequiredMixin, ProtectedDeleteMixin, DeleteView):
    """Only possible while no doctor belongs to the department (PROTECT)."""

    allowed_roles = [Role.ADMIN]
    model = Department
    success_url = reverse_lazy("staff:department_list")
    protected_message = "This department still has doctors. Move or remove them first."


# --- Doctors ------------------------------------------------------------------------


class DoctorListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = ALL_ROLES
    model = Doctor
    paginate_by = 10
    search_fields = [
        "user__first_name",
        "user__last_name",
        "specialization",
        "license_number",
        "department__name",
    ]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("user", "department")
        department = self.request.GET.get("department")
        if department:
            queryset = queryset.filter(department_id=department)
        if self.request.GET.get("show") != "all":
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = Department.objects.all()
        context["selected_department"] = self.request.GET.get("department", "")
        context["show_all"] = self.request.GET.get("show") == "all"
        return context


class DoctorDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = ALL_ROLES
    model = Doctor

    def get_queryset(self):
        return super().get_queryset().select_related("user", "department")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        appointments = self.object.appointments.select_related("patient")
        context["upcoming"] = appointments.filter(
            appointment_date__gte=today, status="SCHEDULED"
        ).order_by("appointment_date", "appointment_time")[:10]
        context["stats"] = appointments.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status="COMPLETED")),
            patients=Count("patient", distinct=True),
        )
        return context


class DoctorCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN]
    model = Doctor
    form_class = DoctorForm
    success_message = "Doctor profile was created."


class DoctorUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN]
    model = Doctor
    form_class = DoctorForm
    success_message = "Doctor profile was updated."


class DoctorDeleteView(RoleRequiredMixin, DetailView):
    """'Delete' for doctors: deactivate so past appointments keep their doctor."""

    allowed_roles = [Role.ADMIN]
    model = Doctor
    template_name = "staff/doctor_confirm_delete.html"

    def post(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor.is_active = False
        doctor.is_available = False
        doctor.save(update_fields=["is_active", "is_available"])
        messages.success(request, f"{doctor} was deactivated.")
        return redirect("staff:doctor_list")
