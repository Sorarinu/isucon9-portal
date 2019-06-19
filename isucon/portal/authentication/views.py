import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from isucon.portal.authentication.models import Team, User
from isucon.portal.authentication.forms import TeamRegisterForm, JoinToTeamForm

PASSWORD_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
PASSWORD_LENGTH = 20
MAX_TEAM_MEMBER_NUM = 3

@login_required
def create_team(request):
    user = request.user
    form = TeamRegisterForm(request.POST or None)
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "create_team.html", {'form': form})


    # team = Team()
    # team.name = form.cleaned_data['name']
    password = ''.join(random.choice(PASSWORD_LETTERS) for i in range(PASSWORD_LENGTH))

    # if len(Team.objects.filter(name=request.POST['team_name'])) > 0:
    #     raise ValidationError('team name already exists')


    team = Team.objects.create(name=form.cleaned_data['name'], password=password, owner=user)

    user.team = team
    user.display_name = form.cleaned_data['owner']
    user.save()

    return render(request, "team_created.html", {'team_name': team.name, 'team_password': team.password, 'team_id': team.id})

@login_required
def join_team(request):
    user = request.user
    form = JoinToTeamForm(request.POST or None)
    print(form.is_valid())
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "join_team.html", {'form': form})


    team_id = form.cleaned_data['team_id']
    team_password = form.cleaned_data['team_password']
    
    team = Team.objects.get(id=int(team_id), password=team_password)

    if team is None:
        raise RuntimeError('チーム番号かチームパスワードが間違っています')
    
    if len(User.objects.filter(team=team)) >= MAX_TEAM_MEMBER_NUM:
        raise RuntimeError('このチームにはこれ以上メンバーを追加できません')

    user.team = team
    user.save()


    context = {
        "team_name": team.name,
        "team_id": team.id,
    }
    
    return render(request, "team_joined.html", context)
