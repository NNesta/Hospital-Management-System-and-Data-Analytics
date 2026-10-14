import datetime

from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin
from appointments.models import Appointment
from staff.models import Department, Doctor


def default_date_from():
    return timezone.localdate() - datetime.timedelta(days=90)


class ReportFilterForm(BootstrapFormMixin, forms.Form):
    date_from = forms.DateField(required=False, label="From", widget=forms.DateInput())
    date_to = forms.DateField(required=False, label="To", widget=forms.DateInput())
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, empty_label="All departments")
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.none(), required=False, empty_label="All doctors")
    status = forms.ChoiceField(required=False, choices=[("", "All statuses")] + Appointment.Status.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = Doctor.objects.select_related("user").order_by("user__first_name")

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("date_from"), cleaned.get("date_to")
        if start and end and start > end:
            self.add_error("date_to", "The end date must be after the start date.")
        return cleaned

    @classmethod
    def from_request(cls, request):
        """Bind GET params, defaulting to the last 90 days on first visit."""
        data = request.GET.copy()
        if not data:
            data["date_from"] = default_date_from().isoformat()
            data["date_to"] = timezone.localdate().isoformat()
        return cls(data)
