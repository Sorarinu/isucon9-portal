from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.core import files
import requests

from isucon.portal.authentication.models import Team, User
from isucon.portal.authentication.forms import TeamRegisterForm, JoinToTeamForm
from isucon.portal.authentication.decorators import team_is_authenticated, check_registration


@check_registration
@login_required
def create_team(request):
    user = request.user
    form = TeamRegisterForm(request.POST or None, request.FILES or None, user=user)
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "create_team.html", {'form': form, 'username': request.user, 'email': request.user.email})

    form.save()

    return redirect("team_information")

@check_registration
@login_required
def join_team(request):
    user = request.user
    form = JoinToTeamForm(request.POST or None, request.FILES or None, user=user)

    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "join_team.html", {'form': form, 'username': request.user})

    form.save()

    return redirect("team_information")

@team_is_authenticated
def team_information(request):
    team = request.user.team

    team_members = User.objects.filter(team=team)
    context = {'team_members': team_members}

    return render(request, "team_information.html", context)
