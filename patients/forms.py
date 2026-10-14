from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin

from .models import Patient


class PatientForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "blood_group",
            "phone",
            "email",
            "national_id",
            "district",
            "address",
            "insurance_provider",
            "insurance_number",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]
        labels = {
            "national_id": "National ID (Indangamuntu)",
        }
        widgets = {
            "date_of_birth": forms.DateInput(),
            "phone": forms.TextInput(attrs={"placeholder": "+250 78x xxx xxx"}),
            "emergency_contact_phone": forms.TextInput(attrs={"placeholder": "+250 78x xxx xxx"}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        if dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean(self):
        cleaned = super().clean()
        provider = cleaned.get("insurance_provider")
        if provider and provider != Patient.Insurance.NONE and not cleaned.get("insurance_number"):
            self.add_error("insurance_number", "Enter the insurance or Mutuelle membership number.")
        return cleaned
