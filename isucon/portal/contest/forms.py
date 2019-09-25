import ipaddress

from django import forms
from django.core.validators import RegexValidator

from isucon.portal.authentication.decorators import is_registration_available
from isucon.portal.authentication.models import Team, User
from isucon.portal.contest.models import Server

def global_ip_validator(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        raise forms.ValidationError("IPv4アドレスではありません")
    if address.is_global:
        return value
    raise forms.ValidationError("グローバルIPではありません")

def private_ip_validator(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        raise forms.ValidationError("IPv4アドレスではありません")
    if address.is_private:
        return value
    raise forms.ValidationError("プライベートIPではありません")


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "participate_at", )

    participate_at = forms.DateField(
        label="参加日選択",
        input_formats=["%Y-%m-%d"],
        widget=forms.Select(choices=Team.PARTICIPATE_AT_CHOICES),
        required=True,
    )

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
            raise forms.ValidationError("Invalid Server ID")

        return data

    def save(self):
        Server.objects.filter(team=self.team).update(is_bench_target=False)
        Server.objects.filter(id=self.cleaned_data["target"], team=self.team).update(is_bench_target=True)

class ServerAddForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ("hostname", "global_ip", "private_ip")

    global_ip = forms.CharField(required=True, validators=[global_ip_validator], )
    private_ip = forms.CharField(required=False, validators=[private_ip_validator], )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if Server.objects.filter(team=self.team).count() >= 3:
            raise forms.ValidationError("すでに3台登録されています")

        return cleaned_data

    def clean_hostname(self):
        hostname = self.cleaned_data.get("hostname", "")

        if len(hostname) == 0:
            raise forms.ValidationError("ホスト名が空です")

        if Server.objects.filter(team=self.team, hostname=hostname).exists():
            raise forms.ValidationError("同一ホスト名のサーバが登録済みです")

        return hostname

    def save(self):
        instance = super().save(commit=False)
        instance.team = self.team
        instance.save()
        return instance
