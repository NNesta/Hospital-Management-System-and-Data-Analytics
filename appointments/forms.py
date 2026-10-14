from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin
from patients.models import Patient
from staff.models import Doctor

from .models import TIME_SLOTS, Appointment, MedicalRecord


class DoctorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        suffix = "" if obj.is_available else " (unavailable)"
        return f"{obj} - {obj.department.name}{suffix}"


class AppointmentForm(BootstrapFormMixin, forms.ModelForm):
    doctor = DoctorChoiceField(queryset=Doctor.objects.none())

    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "appointment_date", "appointment_time", "reason"]
        labels = {"appointment_date": "Date", "appointment_time": "Time slot"}
        widgets = {
            "appointment_date": forms.DateInput(),
            "appointment_time": forms.Select(
                choices=[("", "---------")] + [(t.strftime("%H:%M:%S"), t.strftime("%H:%M")) for t in TIME_SLOTS]
            ),
            "reason": forms.TextInput(attrs={"placeholder": "e.g. Fever and headache for 3 days"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.order_by("first_name", "last_name")
        self.fields["doctor"].queryset = Doctor.objects.active().select_related("user", "department")

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get("doctor")
        day = cleaned.get("appointment_date")
        slot = cleaned.get("appointment_time")

        if day:
            now = timezone.localtime()
            if day < now.date():
                self.add_error("appointment_date", "Appointments cannot be booked in the past.")
            elif day == now.date() and slot and slot < now.time():
                self.add_error("appointment_time", "That time has already passed today.")

        if doctor and not doctor.is_available:
            self.add_error("doctor", f"{doctor} is not taking appointments at the moment.")

        if doctor and day and slot:
            clash = Appointment.objects.filter(doctor=doctor, appointment_date=day, appointment_time=slot)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                # Friendly message for the UniqueConstraint "unique_doctor_slot".
                self.add_error(
                    "appointment_time",
                    f"{doctor} is already booked on {day:%d %b %Y} at {slot:%H:%M}. Choose another slot.",
                )
        return cleaned


class MedicalRecordForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["symptoms", "diagnosis", "treatment_plan", "notes", "follow_up_date"]
        widgets = {
            "follow_up_date": forms.DateInput(),
            "diagnosis": forms.TextInput(attrs={"placeholder": "e.g. Uncomplicated malaria (B54)"}),
        }

    def clean_follow_up_date(self):
        follow_up = self.cleaned_data.get("follow_up_date")
        if follow_up and follow_up < timezone.localdate():
            raise forms.ValidationError("Follow-up date cannot be in the past.")
        return follow_up


class AppointmentFilterForm(forms.Form):
    """Filters shown above the appointment list (GET)."""

    WHEN_CHOICES = [("", "Any date"), ("today", "Today"), ("upcoming", "Upcoming"), ("past", "Past")]

    q = forms.CharField(required=False)
    status = forms.ChoiceField(required=False, choices=[("", "Any status")] + Appointment.Status.choices)
    when = forms.ChoiceField(required=False, choices=WHEN_CHOICES)
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def filter(self, queryset):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        today = timezone.localdate()
        if data["status"]:
            queryset = queryset.filter(status=data["status"])
        if data["when"] == "today":
            queryset = queryset.filter(appointment_date=today)
        elif data["when"] == "upcoming":
            queryset = queryset.filter(appointment_date__gte=today)
        elif data["when"] == "past":
            queryset = queryset.filter(appointment_date__lt=today)
        if data["date"]:
            queryset = queryset.filter(appointment_date=data["date"])
        return queryset
