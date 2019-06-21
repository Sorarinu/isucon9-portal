import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from isucon.portal.authentication.models import Team, User
from isucon.portal.authentication.forms import TeamRegisterForm, JoinToTeamForm
from isucon.portal import settings


@login_required
def create_team(request):
    user = request.user
    form = TeamRegisterForm(request.POST or None)
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "create_team.html", {'form': form, 'username': request.user, 'email': request.user.email})


    # パスワードとして使う文字群から指定文字数ランダムに選択してチームパスワードとする
    password = ''.join(random.choice(settings.PASSWORD_LETTERS) for i in range(settings.PASSWORD_LENGTH))

    team = Team.objects.create(name=form.cleaned_data['name'], password=password, owner=user)

    user.team = team
    user.display_name = form.cleaned_data['owner']
    user.email = form.cleaned_data['owner_email']
    user.save()

    

    context = {
        "team_name": team.name,
        "team_password": team.password,
        "team_id": team.id,
        'username': request.user,
        'email': request.user.email,
    }

    return render(request, "team_created.html", context)

@login_required
def join_team(request):
    user = request.user
    form = JoinToTeamForm(request.POST or None)
    print(form.is_valid())
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "join_team.html", {'form': form, 'username': request.user})


    team_id = form.cleaned_data['team_id']
    team_password = form.cleaned_data['team_password']
    
    team = Team.objects.get(id=int(team_id), password=team_password)

    user.team = team
    user.save()


    context = {
        "team_name": team.name,
        "team_id": team.id,
        'username': request.user,
    }
    
    return render(request, "team_joined.html", context)
