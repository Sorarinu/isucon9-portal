import random
import requests
import uuid
from io import BytesIO
from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings
from django.core import files

from isucon.portal.authentication.models import Team, User
from isucon.portal import settings

class TeamRegisterForm(forms.Form):
    name = forms.CharField(
        label="チーム名",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'Team ISUCON'}),
    )
    display_name = forms.CharField(
        label="参加者名 (ハンドルネーム可)",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'ISUCON Taro', 'id': 'display_name'}),
    )
    is_student = forms.BooleanField(
        label="あなたが学生の場合、チェックを入れてください",
        required=False,
    )
    is_import_github_icon = forms.BooleanField(
        label="アイコンをGithubから取り込む",
        required=False,
    )
    user_icon = forms.ImageField(
        label="アイコン",
        required=False,
    )
    email = forms.CharField(
        label="代表者メールアドレス (公開されません)",
        max_length=256,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'type': 'email', 'placeholder': 'isucon@example.com', 'id': 'email'}),
    )
    is_ok = forms.BooleanField(
        label="注意を読みましたチェック",
        required=True,
    )
    participate_at = forms.DateField(
        label="参加日選択",
        input_formats=["%Y-%m-%d"],
        widget=forms.Select(choices=Team.PARTICIPATE_AT_CHOICES),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_user_icon(self):
        if self.cleaned_data['user_icon'] is None:
            return None
        return check_uploaded_filesize(self.cleaned_data['user_icon'])

    def clean(self):
        cleaned_data = super(TeamRegisterForm, self).clean()
        if not cleaned_data['is_import_github_icon'] and cleaned_data['user_icon'] is None:
            raise ValidationError('アイコンが選択されていません')

        return cleaned_data

    def save(self):
        user = self.user

        # パスワードとして使う文字群から指定文字数ランダムに選択してチームパスワードとする
        password = ''.join(random.choice(settings.PASSWORD_LETTERS) for i in range(settings.PASSWORD_LENGTH))

        team = Team.objects.create(name=self.cleaned_data['name'], participate_at=self.cleaned_data['participate_at'], password=password, owner=user)

        user.team = team
        user.is_student = self.cleaned_data['is_student']
        user.display_name = self.cleaned_data['display_name']
        user.email = self.cleaned_data['email']

        if self.cleaned_data['is_import_github_icon']:
            resp = requests.get("https://github.com/%s.png" % user.username)
            if resp.status_code != requests.codes.ok:
                raise RuntimeError('icon fetch failed')

            file_name = "{}_{}.png".format(user.id, str(uuid.uuid4()))

            fp = BytesIO()
            fp.write(resp.content)
            user.icon.save(file_name, files.File(fp))
        else:
            user.icon = self.cleaned_data['user_icon']
        user.save()

        return user

class JoinToTeamForm(forms.Form):
    display_name = forms.CharField(
        label="参加者名 (ハンドルネーム可)",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': "input", 'placeholder': 'ISUCON Taro', 'id': 'display_name'}),
    )
    is_student = forms.BooleanField(
        label="あなたが学生の場合、チェックを入れてください",
        required=False,
    )
    user_icon = forms.ImageField(
        label="アイコン",
        required=False,
    )
    is_import_github_icon = forms.BooleanField(
        label="アイコンをGithubから取り込む",
        required=False,
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_user_icon(self):
        if self.cleaned_data['user_icon'] is None:
            return None
        return check_uploaded_filesize(self.cleaned_data['user_icon'])

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

    def save(self):
        user = self.user
        team_id = self.cleaned_data['team_id']
        team_password = self.cleaned_data['team_password']

        team = Team.objects.get(id=int(team_id), password=team_password)

        user.team = team
        user.is_student = self.cleaned_data['is_student']
        user.display_name = self.cleaned_data['display_name']
        if self.cleaned_data['is_import_github_icon']:
            resp = requests.get("https://github.com/%s.png" % user.username)
            if resp.status_code != requests.codes.ok:
                raise RuntimeError('icon fetch failed')

            file_name = "{}_{}.png".format(user.id, str(uuid.uuid4()))

            fp = BytesIO()
            fp.write(resp.content)
            user.icon.save(file_name, files.File(fp))
        else:
            user.icon = self.cleaned_data['user_icon']
        user.save()

        return user

def check_uploaded_filesize(content):
    if content.size > settings.MAX_UPLOAD_SIZE:
        raise forms.ValidationError(('ファイルサイズが大きすぎます。'))
    return content
