from django import forms

from isucon.portal.authentication.models import Team, User

class TeamRegisterForm(forms.Form):
    name = forms.CharField(
        label="チーム名",
        max_length=100,
        required=True,
    )
    owner = forms.CharField(
        label="代表者名",
        max_length=100,
        required=True,
    )
    is_ok = forms.BooleanField(
        label="注意を読みましたチェック",
        required=True,
    )

class JoinToTeamForm(forms.Form):
    team_id = forms.IntegerField(
        label="チーム番号",
        required=True,
    )
    team_password = forms.CharField(
        label="チームパスワード",
        max_length=100,
        required=True,
    )
    display_name = forms.CharField(
        label="公開する参加者名",
        max_length=100,
        required=True,
    )
    is_ok = forms.BooleanField(
        label="注意を読みましたチェック",
        required=True,
    )

