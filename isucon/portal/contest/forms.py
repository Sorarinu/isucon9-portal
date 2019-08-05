from django import forms
from django.core.validators import RegexValidator

from isucon.portal.authentication.models import Team

alibaba_account_validator = RegexValidator(r'^\d{16}$', "Invalid Account ID Format")

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("alibaba_account", )


    alibaba_account = forms.CharField(required=True, validators=[alibaba_account_validator], )
