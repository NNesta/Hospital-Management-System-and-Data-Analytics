import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from patients.models import Patient
from staff.models import Doctor

# Outpatient clinic slots: 08:00 to 16:30 every 30 minutes.
TIME_SLOTS = [datetime.time(h, m) for h in range(8, 17) for m in (0, 30)]


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No-show"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    appointment_date = models.DateField(db_index=True)
    appointment_time = models.TimeField()
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_appointments",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]
        verbose_name = "appointment"
        verbose_name_plural = "appointments"
        constraints = [
            # Blocks double booking at database level.
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "appointment_time"],
                name="unique_doctor_slot",
            ),
        ]

    def __str__(self):
        return f"{self.patient.full_name} with {self.doctor} on {self.appointment_date:%d %b %Y} {self.appointment_time:%H:%M}"

    def get_absolute_url(self):
        return reverse("appointments:detail", args=[self.pk])

    @property
    def is_scheduled(self):
        return self.status == self.Status.SCHEDULED

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def is_today(self):
        return self.appointment_date == timezone.localdate()


class MedicalRecord(models.Model):
    """The consultation note a doctor writes when completing an appointment."""

    appointment = models.OneToOneField(Appointment, on_delete=models.PROTECT, related_name="medical_record")
    symptoms = models.TextField()
    diagnosis = models.CharField(max_length=255)
    treatment_plan = models.TextField()
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "medical record"
        verbose_name_plural = "medical records"

    def __str__(self):
        return f"{self.diagnosis} - {self.appointment.patient.full_name}"

    def get_absolute_url(self):
        return reverse("appointments:record_detail", args=[self.pk])

    @property
    def patient(self):
        return self.appointment.patient

    @property
    def doctor(self):
        return self.appointment.doctor
