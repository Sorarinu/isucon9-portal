from django import forms
from django.core.validators import RegexValidator

from isucon.portal.authentication.decorators import is_registration_available
from isucon.portal.authentication.models import Team

alibaba_account_validator = RegexValidator(r'^\d{16}$', "Invalid Account ID Format")

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "alibaba_account", )

    alibaba_account = forms.CharField(required=True, validators=[alibaba_account_validator], )

    def __init__(self, *args, **kwargs):
        self.is_registration_available = is_registration_available()

        super().__init__(*args, **kwargs)

        if not self.is_registration_available:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].widget.attrs['class'] = 'is-static'

    def clean_name(self):
        if not self.is_registration_available:
            return self.instance.name
        return self.cleaned_data.get("name", "")
