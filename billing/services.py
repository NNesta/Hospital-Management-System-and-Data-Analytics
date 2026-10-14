"""Billing business logic: build an invoice from a completed visit."""

from django.db import transaction

from appointments.models import Appointment
from pharmacy.models import Prescription, PrescriptionItem

from .models import Invoice, InvoiceItem


class InvoiceError(Exception):
    """Raised when an invoice cannot be generated; message is user-facing."""


def generate_invoice(appointment: Appointment, user) -> Invoice:
    """One Consultation item from the doctor's fee, plus one Medicine item per
    dispensed PrescriptionItem of the visit."""
    if appointment.status != Appointment.Status.COMPLETED:
        raise InvoiceError("Only completed appointments can be invoiced.")
    if Invoice.objects.filter(appointment=appointment).exists():
        raise InvoiceError("This appointment already has an invoice.")

    doctor = appointment.doctor
    with transaction.atomic():
        invoice = Invoice.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            created_by=user,
        )
        items = [
            InvoiceItem(
                invoice=invoice,
                item_type=InvoiceItem.ItemType.CONSULTATION,
                description=f"Consultation - {doctor} ({doctor.department.name})",
                quantity=1,
                unit_price=doctor.consultation_fee,
            )
        ]
        dispensed = PrescriptionItem.objects.filter(
            prescription__medical_record__appointment=appointment,
            prescription__status=Prescription.Status.DISPENSED,
        ).select_related("medicine")
        for line in dispensed:
            items.append(
                InvoiceItem(
                    invoice=invoice,
                    item_type=InvoiceItem.ItemType.MEDICINE,
                    description=line.medicine.name,
                    quantity=line.quantity,
                    unit_price=line.medicine.unit_price,
                    medicine=line.medicine,
                )
            )
        InvoiceItem.objects.bulk_create(items)
    return invoice
