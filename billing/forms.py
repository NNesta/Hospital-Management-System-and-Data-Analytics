from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from accounts.forms import BootstrapFormMixin
from appointments.models import Appointment
from patients.models import Patient

from .models import Invoice, InvoiceItem, Payment


class InvoiceForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["patient", "appointment", "issue_date", "due_date", "notes"]
        widgets = {
            "issue_date": forms.DateInput(),
            "due_date": forms.DateInput(),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.order_by("first_name", "last_name")
        # Completed visits that are not billed yet (plus this invoice's own visit).
        visits = Appointment.objects.filter(status=Appointment.Status.COMPLETED, invoice__isnull=True)
        if self.instance.appointment_id:
            visits = visits | Appointment.objects.filter(pk=self.instance.appointment_id)
        self.fields["appointment"].queryset = visits.select_related("patient", "doctor__user").order_by(
            "-appointment_date"
        )
        self.fields["appointment"].help_text = "Optional: link a completed visit."

    def clean(self):
        cleaned = super().clean()
        patient, visit = cleaned.get("patient"), cleaned.get("appointment")
        if patient and visit and visit.patient_id != patient.pk:
            self.add_error("appointment", "This visit belongs to a different patient.")
        issue, due = cleaned.get("issue_date"), cleaned.get("due_date")
        if issue and due and due < issue:
            self.add_error("due_date", "The due date cannot be before the issue date.")
        return cleaned


class InvoiceItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["item_type", "description", "quantity", "unit_price", "medicine"]
        labels = {"unit_price": "Unit price (RWF)"}


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=2,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class PaymentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "reference", "paid_at"]
        labels = {"amount": "Amount (RWF)", "paid_at": "Paid at"}
        widgets = {"paid_at": forms.DateTimeInput()}

    def __init__(self, *args, invoice: Invoice, **kwargs):
        self.invoice = invoice
        super().__init__(*args, **kwargs)
        balance = self.max_amount()
        self.fields["amount"].help_text = f"Outstanding balance: RWF {balance:,.0f}"
        if not self.instance.pk:
            self.initial.setdefault("amount", balance)

    def max_amount(self) -> Decimal:
        """The balance, plus this payment's old amount when editing."""
        balance = self.invoice.balance
        if self.instance.pk:
            balance += Payment.objects.get(pk=self.instance.pk).amount
        return balance

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("The amount must be greater than zero.")
        if amount > self.max_amount():
            raise forms.ValidationError(f"The amount is above the balance of RWF {self.max_amount():,.0f}.")
        return amount

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("method") in (Payment.Method.MOBILE_MONEY, Payment.Method.INSURANCE) and not cleaned.get(
            "reference"
        ):
            self.add_error("reference", "Enter the MoMo transaction ID or insurance claim number.")
        return cleaned
