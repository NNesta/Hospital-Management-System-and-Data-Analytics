from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse

from .validators import validate_rwanda_phone


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    RECEPTIONIST = "RECEPTIONIST", "Receptionist"
    DOCTOR = "DOCTOR", "Doctor"
    PHARMACIST = "PHARMACIST", "Pharmacist"
    ACCOUNTANT = "ACCOUNTANT", "Accountant"


class HMSUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Staff account. Every login belongs to exactly one of the five roles."""

    phone = models.CharField(max_length=20, blank=True, validators=[validate_rwanda_phone])
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RECEPTIONIST)

    objects = HMSUserManager()

    class Meta:
        ordering = ["first_name", "last_name", "username"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.get_full_name() or self.username

    def get_absolute_url(self):
        return reverse("accounts:user_detail", args=[self.pk])

    def has_role(self, *roles):
        return self.is_authenticated and self.role in roles

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN

    @property
    def is_doctor(self):
        return self.role == Role.DOCTOR

    @property
    def role_color(self):
        return {
            Role.ADMIN: "danger",
            Role.RECEPTIONIST: "info",
            Role.DOCTOR: "success",
            Role.PHARMACIST: "warning",
            Role.ACCOUNTANT: "primary",
        }.get(self.role, "secondary")
