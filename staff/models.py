from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.validators import validate_rwanda_phone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True, help_text="e.g. Block B, 1st floor")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "department"
        verbose_name_plural = "departments"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("staff:department_detail", args=[self.pk])


class DoctorQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def bookable(self):
        return self.filter(is_active=True, is_available=True)


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="doctor_profile",
        limit_choices_to={"role": Role.DOCTOR},
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="doctors")
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(
        max_length=30, unique=True, help_text="Rwanda Medical and Dental Council (RMDC) licence"
    )
    phone = models.CharField(max_length=20, validators=[validate_rwanda_phone])
    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("5000"))
    is_available = models.BooleanField(default=True, help_text="Can take new appointments")
    is_active = models.BooleanField(default=True, help_text="Untick instead of deleting")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    objects = DoctorQuerySet.as_manager()

    class Meta:
        ordering = ["user__first_name", "user__last_name"]
        verbose_name = "doctor"
        verbose_name_plural = "doctors"
        constraints = [
            models.CheckConstraint(
                condition=Q(consultation_fee__gt=0), name="doctor_consultation_fee_positive"
            ),
        ]

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

    def get_absolute_url(self):
        return reverse("staff:doctor_detail", args=[self.pk])

    @property
    def full_name(self):
        return self.user.get_full_name()
