from django import forms

from accounts.forms import BootstrapFormMixin
from accounts.models import Role, User

from .models import Department, Doctor


class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "location", "description"]


class DoctorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            "user",
            "department",
            "specialization",
            "license_number",
            "phone",
            "consultation_fee",
            "is_available",
            "is_active",
        ]
        labels = {"user": "Doctor account", "consultation_fee": "Consultation fee (RWF)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only doctor-role users without a profile yet (plus the current one on edit).
        users = User.objects.filter(role=Role.DOCTOR, is_active=True, doctor_profile__isnull=True)
        if self.instance.pk:
            users = users | User.objects.filter(pk=self.instance.user_id)
        self.fields["user"].queryset = users.order_by("first_name", "last_name")
        self.fields["user"].help_text = "Create the login first under Users with the Doctor role."
        self.fields["department"].queryset = Department.objects.order_by("name")
