from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from isucon.portal.authentication.models import Team, User
from isucon.portal import settings

class TeamRegisterForm(forms.Form):
    name = forms.CharField(
        label="チーム名",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'Team ISUCON'}),
    )
    owner = forms.CharField(
        label="代表者名(ハンドルネーム可)",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'ISUCON Taro'}),
    )
    owner_email = forms.CharField(
        label="代表者メールアドレス(公開されません)",
        max_length=256,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'type': 'email', 'placeholder': 'isucon@example.com'}),
    )
    is_ok = forms.BooleanField(
        label="注意を読みましたチェック",
        required=True,
    )

class JoinToTeamForm(forms.Form):
    display_name = forms.CharField(
        label="公開する参加者名",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'ISUCON Taro'}),
    )
    team_id = forms.IntegerField(
        label="チーム番号",
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': '12345'}),
    )
    team_password = forms.CharField(
        label="チームパスワード",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input"}),
    )
    is_ok = forms.BooleanField(
        label="注意を読みましたチェック",
        required=True,
    )

    def clean(self):
        cleaned_data = super(JoinToTeamForm, self).clean()
        team_id = cleaned_data.get('team_id')
        team_password = cleaned_data.get('team_password')
        
        try:
            team = Team.objects.get(id=int(team_id), password=team_password)
        except ObjectDoesNotExist:
            raise ValidationError('チーム番号かチームパスワードが間違っています')
        
        if len(User.objects.filter(team=team)) >= settings.MAX_TEAM_MEMBER_NUM:
            raise ValidationError('このチームにはこれ以上メンバーを追加できません')
        
        return cleaned_data

