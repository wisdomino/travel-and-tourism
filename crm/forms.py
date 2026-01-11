from django import forms
import phonenumbers

from .models import Organization, Branch, Program, ApplicationType


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for _, field in self.fields.items():
            widget = field.widget
            if widget.__class__.__name__ in ["Select", "SelectMultiple"]:
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-select").strip()
            else:
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-control").strip()


class ClientCreateForm(BootstrapFormMixin, forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())
    full_name = forms.CharField(max_length=200)
    phone_e164 = forms.CharField(
        max_length=30,
        help_text="Use international format e.g. +2348012345678",
    )
    email = forms.EmailField(required=False)
    timezone = forms.CharField(max_length=64, initial="Africa/Lagos")
    preferred_language = forms.CharField(max_length=20, initial="en")
    source = forms.CharField(max_length=80, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_phone_e164(self):
        phone = self.cleaned_data["phone_e164"].strip()
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                raise forms.ValidationError(
                    "Invalid phone number. Use E.164 format, e.g. +2348012345678"
                )
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise forms.ValidationError(
                "Invalid phone number format. Use E.164 format, e.g. +2348012345678"
            )


class CaseCreateForm(BootstrapFormMixin, forms.Form):
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=False)
    program = forms.ModelChoiceField(queryset=Program.objects.filter(is_active=True), required=False)

    destination_country_code = forms.CharField(max_length=2, help_text="ISO code e.g. CA, GB, US")
    application_type = forms.ChoiceField(choices=ApplicationType.choices)
    assigned_officer_id = forms.IntegerField(required=False, help_text="Django user id (optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_destination_country_code(self):
        code = self.cleaned_data["destination_country_code"].strip().upper()
        if len(code) != 2:
            raise forms.ValidationError("Country code must be 2 letters, e.g. CA")
        return code
