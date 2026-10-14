from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.validators import validate_rwanda_national_id, validate_rwanda_phone

# Rwanda's 5 provinces and 30 districts (grouped choices render as <optgroup>).
DISTRICT_CHOICES = [
    ("Kigali City", [(d, d) for d in ["Gasabo", "Kicukiro", "Nyarugenge"]]),
    (
        "Northern Province",
        [(d, d) for d in ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"]],
    ),
    (
        "Southern Province",
        [
            (d, d)
            for d in ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"]
        ],
    ),
    (
        "Eastern Province",
        [(d, d) for d in ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"]],
    ),
    (
        "Western Province",
        [(d, d) for d in ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"]],
    ),
]
DISTRICT_TO_PROVINCE = {d: province for province, items in DISTRICT_CHOICES for d, _ in items}


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"
        UNKNOWN = "UNK", "Unknown"

    class Insurance(models.TextChoices):
        MUTUELLE = "MUTUELLE", "Mutuelle de Santé (CBHI)"
        RSSB = "RSSB", "RSSB (formerly RAMA)"
        MMI = "MMI", "MMI (Military Medical Insurance)"
        PRIVATE = "PRIVATE", "Private insurer"
        NONE = "NONE", "None (self-pay)"

    patient_code = models.CharField(max_length=12, unique=True, null=True, blank=True, editable=False)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN)
    phone = models.CharField(max_length=20, validators=[validate_rwanda_phone])
    email = models.EmailField(blank=True)
    district = models.CharField(max_length=30, choices=DISTRICT_CHOICES)
    address = models.CharField(max_length=200, help_text="Sector, cell and village, e.g. Kimironko, Bibare, Isangano")
    national_id = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_rwanda_national_id],
        help_text="16 digits. Leave empty for children.",
    )
    insurance_provider = models.CharField(max_length=10, choices=Insurance.choices, default=Insurance.MUTUELLE)
    insurance_number = models.CharField(max_length=30, blank=True)
    emergency_contact_name = models.CharField(max_length=120)
    emergency_contact_phone = models.CharField(max_length=20, validators=[validate_rwanda_phone])
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_patients",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "patient"
        verbose_name_plural = "patients"

    def __str__(self):
        return f"{self.full_name} ({self.patient_code})"

    def get_absolute_url(self):
        return reverse("patients:detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.national_id == "":
            self.national_id = None  # keep the unique index happy for children
        super().save(*args, **kwargs)
        if not self.patient_code:
            # Readable code from the primary key: PAT-00001.
            self.patient_code = f"PAT-{self.pk:05d}"
            Patient.objects.filter(pk=self.pk).update(patient_code=self.patient_code)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.localdate()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def province(self):
        return DISTRICT_TO_PROVINCE.get(self.district, "")
