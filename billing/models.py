from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment
from patients.models import Patient
from pharmacy.models import Medicine

MONEY = DecimalField(max_digits=12, decimal_places=2)
ZERO = Value(Decimal("0.00"), output_field=MONEY)


def default_due_date():
    return timezone.localdate() + timedelta(days=7)


class InvoiceQuerySet(models.QuerySet):
    def with_totals(self):
        """Annotate total_amount, paid_amount and balance_amount in SQL.

        Subqueries avoid the double counting a JOIN on items *and* payments causes.
        """
        items = (
            InvoiceItem.objects.filter(invoice=OuterRef("pk"))
            .values("invoice")
            .annotate(s=Sum(ExpressionWrapper(F("quantity") * F("unit_price"), output_field=MONEY)))
            .values("s")
        )
        paid = Payment.objects.filter(invoice=OuterRef("pk")).values("invoice").annotate(s=Sum("amount")).values("s")
        return self.annotate(
            total_amount=Coalesce(Subquery(items, output_field=MONEY), ZERO),
            paid_amount=Coalesce(Subquery(paid, output_field=MONEY), ZERO),
        ).annotate(balance_amount=ExpressionWrapper(F("total_amount") - F("paid_amount"), output_field=MONEY))

    def open(self):
        return self.exclude(status=Invoice.Status.PAID)


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"
        PAID = "PAID", "Paid"

    invoice_number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="invoices")
    appointment = models.OneToOneField(
        Appointment, on_delete=models.PROTECT, null=True, blank=True, related_name="invoice"
    )
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(default=default_due_date)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.UNPAID, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_invoices",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    objects = InvoiceQuerySet.as_manager()

    class Meta:
        ordering = ["-issue_date", "-pk"]
        verbose_name = "invoice"
        verbose_name_plural = "invoices"

    def __str__(self):
        return self.invoice_number or f"Invoice #{self.pk}"

    def get_absolute_url(self):
        return reverse("billing:invoice_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.invoice_number:
            # Readable number from the primary key: INV-2026-00001.
            self.invoice_number = f"INV-{self.issue_date.year}-{self.pk:05d}"
            Invoice.objects.filter(pk=self.pk).update(invoice_number=self.invoice_number)

    # Computed values are properties, not columns. They use .all() so a
    # prefetch_related("items", "payments") in list views avoids extra queries.
    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    @property
    def amount_paid(self):
        return sum((payment.amount for payment in self.payments.all()), Decimal("0.00"))

    @property
    def balance(self):
        return self.total - self.amount_paid

    @property
    def is_overdue(self):
        return self.status != self.Status.PAID and self.due_date < timezone.localdate()

    def refresh_status(self, save=True):
        """Unpaid -> Partially paid -> Paid, from the sum of payments."""
        paid = self.payments.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        total = self.items.aggregate(s=Sum(F("quantity") * F("unit_price"), output_field=MONEY))["s"] or Decimal("0")
        if paid <= 0:
            status = self.Status.UNPAID
        elif paid < total:
            status = self.Status.PARTIALLY_PAID
        else:
            status = self.Status.PAID
        if status != self.status:
            self.status = status
            if save:
                self.save(update_fields=["status"])
        return status


class InvoiceItem(models.Model):
    class ItemType(models.TextChoices):
        CONSULTATION = "CONSULTATION", "Consultation"
        MEDICINE = "MEDICINE", "Medicine"
        OTHER = "OTHER", "Other"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=15, choices=ItemType.choices, default=ItemType.OTHER)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    medicine = models.ForeignKey(
        Medicine, on_delete=models.PROTECT, null=True, blank=True, related_name="invoice_items"
    )

    class Meta:
        ordering = ["pk"]
        verbose_name = "invoice item"
        verbose_name_plural = "invoice items"
        constraints = [
            models.CheckConstraint(condition=Q(unit_price__gt=0), name="invoice_item_unit_price_positive"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="invoice_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.description} x {self.quantity}"

    @property
    def line_total(self):
        return (self.quantity or 0) * (self.unit_price or Decimal("0"))


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile money (MTN MoMo / Airtel Money)"
        CARD = "CARD", "Card"
        INSURANCE = "INSURANCE", "Insurance (Mutuelle / RSSB / MMI)"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=15, choices=Method.choices, default=Method.MOBILE_MONEY)
    reference = models.CharField(max_length=60, blank=True, help_text="MoMo transaction ID, receipt or claim number")
    paid_at = models.DateTimeField(default=timezone.now, db_index=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_payments",
    )

    class Meta:
        ordering = ["-paid_at"]
        verbose_name = "payment"
        verbose_name_plural = "payments"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),
        ]

    def __str__(self):
        return f"RWF {self.amount:,.0f} on {self.invoice}"

    def get_absolute_url(self):
        return reverse("billing:payment_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.refresh_status()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.refresh_status()
        return result
