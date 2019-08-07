from django import forms
from django.core.validators import RegexValidator

from isucon.portal.authentication.decorators import is_registration_available
from isucon.portal.authentication.models import Team, User
from isucon.portal.contest.models import Server

alibaba_account_validator = RegexValidator(r'^\d{16}$', "Invalid Account ID Format")

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "participate_at", "alibaba_account", )

    participate_at = forms.DateField(
        label="参加日選択",
        input_formats=["%Y-%m-%d"],
        widget=forms.Select(choices=Team.PARTICIPATE_AT_CHOICES),
        required=True,
    )
    alibaba_account = forms.CharField(required=False, validators=[alibaba_account_validator], )

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


    def clean_participate_at(self):
        if not self.is_registration_available:
            return self.instance.participate_at
        return self.cleaned_data.get("participate_at", None)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["display_name", ]

class UserIconForm(forms.Form):
    icon = forms.ImageField(label="アイコン", required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self):
        self.user.icon = self.cleaned_data['icon']
        self.user.save()
        return self.user

class ServerTargetForm(forms.Form):

    target = forms.IntegerField(label="対象サーバID")

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team")
        super().__init__(*args, **kwargs)

    def clean_target(self):
        data = self.cleaned_data['target']

        if not Server.objects.filter(id=data, team=self.team).exists():
            raise form.ValidationError("Invalid Server ID")

        return data


    def save(self):

        Server.objects.filter(team=self.team).update(is_bench_target=False)
        Server.objects.filter(id=self.cleaned_data["target"], team=self.team).update(is_bench_target=True)
