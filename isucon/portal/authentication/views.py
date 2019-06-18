import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from isucon.portal.authentication.models import Team, User

PASSWORD_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
PASSWORD_LENGTH = 20
MAX_TEAM_MEMBER_NUM = 3

@login_required
def create_team(request):
    user = request.user
    team_name = request.POST['team_name']
    
    if len(Team.objects.filter(name=request.POST['team_name'])) > 0:
        raise RuntimeError('team name already exists')
    
    password = ''.join(random.choice(PASSWORD_LETTERS) for i in range(PASSWORD_LENGTH)) 

    team = Team.objects.create(name=request.POST['team_name'], password=password, owner=user)
    
    user.team = Team.objects.get(name=request.POST['team_name'])
    user.save()


    context = {
        "team_id": team.id,
        "team_name": team_name,
        "team_password": password,
    }
    
    return render(request, "team_created.html", context)

@login_required
def join_team(request):
    user = request.user
    team_id = request.POST['team_id']
    team_password = request.POST['team_password']
    
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
