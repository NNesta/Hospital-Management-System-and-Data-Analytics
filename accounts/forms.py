from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import User


class BootstrapFormMixin:
    """Give every widget its Bootstrap/AdminLTE class and HTML5 input type.

    Used by every ModelForm in the project, so templates can render fields with
    one shared partial (partials/_form_fields.html).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
                css = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()

            if isinstance(widget, forms.DateTimeInput):
                widget.input_type = "datetime-local"
                widget.format = "%Y-%m-%dT%H:%M"
            elif isinstance(widget, forms.DateInput):
                widget.input_type = "date"
                widget.format = "%Y-%m-%d"
            elif isinstance(widget, forms.TimeInput):
                widget.input_type = "time"
                widget.format = "%H:%M"
            elif isinstance(widget, forms.Textarea) and widget.attrs.get("rows") in (None, "10"):
                widget.attrs["rows"] = 3  # Django's default of 10 rows is too tall

    def full_clean(self):
        super().full_clean()
        # Mark invalid inputs so Bootstrap shows the red border + feedback text.
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs["class"] = f"{widget.attrs.get('class', '')} is-invalid"


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class UserCreateForm(BootstrapFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["first_name", "last_name", "role"]:
            self.fields[name].required = True


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role", "is_active"]


class AdminSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass


class OwnPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    pass
