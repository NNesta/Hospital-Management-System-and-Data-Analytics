from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from appointments.models import MedicalRecord


class Medicine(models.Model):
    class Category(models.TextChoices):
        ANTIMALARIAL = "ANTIMALARIAL", "Antimalarial"
        ANTIBIOTIC = "ANTIBIOTIC", "Antibiotic"
        ANALGESIC = "ANALGESIC", "Analgesic / antipyretic"
        ANTIHYPERTENSIVE = "ANTIHYPERTENSIVE", "Antihypertensive"
        ANTIDIABETIC = "ANTIDIABETIC", "Antidiabetic"
        GASTRO = "GASTRO", "Gastrointestinal"
        ANTHELMINTIC = "ANTHELMINTIC", "Anthelmintic"
        RESPIRATORY = "RESPIRATORY", "Respiratory"
        SUPPLEMENT = "SUPPLEMENT", "Vitamin / supplement"
        ANTIHISTAMINE = "ANTIHISTAMINE", "Antihistamine"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=120, unique=True, help_text="Brand or form, e.g. Coartem 20/120 mg tablet")
    generic_name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price per unit in RWF")
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=50)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "medicine"
        verbose_name_plural = "medicines"
        constraints = [
            models.CheckConstraint(condition=Q(unit_price__gt=0), name="medicine_unit_price_positive"),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("pharmacy:medicine_detail", args=[self.pk])

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    @property
    def is_expired(self):
        return self.expiry_date < timezone.localdate()


class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DISPENSED = "DISPENSED", "Dispensed"

    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.PROTECT, related_name="prescriptions")
    medicines = models.ManyToManyField(Medicine, through="PrescriptionItem", related_name="prescriptions")
    issued_at = models.DateTimeField(default=timezone.now, editable=False)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispensed_prescriptions",
    )

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "prescription"
        verbose_name_plural = "prescriptions"

    def __str__(self):
        return f"RX-{self.pk:05d} for {self.patient.full_name}"

    def get_absolute_url(self):
        return reverse("pharmacy:prescription_detail", args=[self.pk])

    @property
    def code(self):
        return f"RX-{self.pk:05d}"

    @property
    def patient(self):
        return self.medical_record.appointment.patient

    @property
    def doctor(self):
        return self.medical_record.appointment.doctor

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def total_cost(self):
        return sum((item.line_total for item in self.items.all()), 0)


class PrescriptionItem(models.Model):
    """Join table that makes Prescription <-> Medicine many-to-many with extra data."""

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name="prescription_items")
    dosage = models.CharField(max_length=60, help_text="e.g. 1 tablet")
    frequency = models.CharField(max_length=60, help_text="e.g. 3 times a day")
    duration_days = models.PositiveIntegerField(default=3)
    quantity = models.PositiveIntegerField(help_text="Units to dispense")

    class Meta:
        ordering = ["pk"]
        verbose_name = "prescription item"
        verbose_name_plural = "prescription items"
        constraints = [
            models.UniqueConstraint(fields=["prescription", "medicine"], name="unique_medicine_per_prescription"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="prescription_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.medicine} x {self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.medicine.unit_price
