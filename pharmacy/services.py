"""Pharmacy business logic kept out of views and templates."""

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Medicine, Prescription


class DispenseError(Exception):
    """Raised when a prescription cannot be dispensed; message is user-facing."""


def dispense_prescription(prescription: Prescription, user) -> Prescription:
    """Deduct stock for every item and mark the prescription Dispensed.

    All-or-nothing: rows are locked with select_for_update() inside one
    transaction, and if any medicine lacks stock nothing changes.
    """
    with transaction.atomic():
        prescription = Prescription.objects.select_for_update().get(pk=prescription.pk)
        if prescription.status != Prescription.Status.PENDING:
            raise DispenseError("This prescription has already been dispensed.")

        items = list(prescription.items.all())
        if not items:
            raise DispenseError("This prescription has no medicines.")

        locked = Medicine.objects.select_for_update().in_bulk([item.medicine_id for item in items])
        short = [
            f"{locked[item.medicine_id].name} (need {item.quantity}, have {locked[item.medicine_id].stock_quantity})"
            for item in items
            if locked[item.medicine_id].stock_quantity < item.quantity
        ]
        if short:
            raise DispenseError("Not enough stock: " + "; ".join(short) + ".")

        for item in items:
            Medicine.objects.filter(pk=item.medicine_id).update(stock_quantity=F("stock_quantity") - item.quantity)

        prescription.status = Prescription.Status.DISPENSED
        prescription.dispensed_at = timezone.now()
        prescription.dispensed_by = user
        prescription.save(update_fields=["status", "dispensed_at", "dispensed_by"])
    return prescription
