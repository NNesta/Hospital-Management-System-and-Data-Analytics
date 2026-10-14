from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from accounts.forms import BootstrapFormMixin

from .models import Medicine, Prescription, PrescriptionItem


class MedicineForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "generic_name", "category", "unit_price", "stock_quantity", "reorder_level", "expiry_date"]
        labels = {"unit_price": "Unit price (RWF)"}
        widgets = {"expiry_date": forms.DateInput()}


class MedicineChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} - RWF {obj.unit_price:,.0f} (stock {obj.stock_quantity})"


class PrescriptionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2, "placeholder": "Advice for the patient or pharmacist"})}


class PrescriptionItemForm(BootstrapFormMixin, forms.ModelForm):
    medicine = MedicineChoiceField(queryset=Medicine.objects.order_by("name"))

    class Meta:
        model = PrescriptionItem
        fields = ["medicine", "dosage", "frequency", "duration_days", "quantity"]
        labels = {"duration_days": "Days"}
        widgets = {
            "dosage": forms.TextInput(attrs={"placeholder": "1 tablet"}),
            "frequency": forms.TextInput(attrs={"placeholder": "3 times a day"}),
        }


class BasePrescriptionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            medicine = form.cleaned_data.get("medicine")
            if medicine in seen:
                form.add_error("medicine", "This medicine is already on the prescription.")
            seen.add(medicine)


# One form, many rows: Prescription + its PrescriptionItems.
PrescriptionItemFormSet = inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    formset=BasePrescriptionItemFormSet,
    extra=2,
    min_num=1,
    validate_min=True,
    can_delete=True,
)
