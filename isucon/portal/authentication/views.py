from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.core import files
from django.http import HttpResponse
from django.contrib.auth.views import LoginView as DjangoLoginView
import requests
import csv

from isucon.portal.authentication.models import Team, User
from isucon.portal.authentication.forms import TeamRegisterForm, JoinToTeamForm
from isucon.portal.authentication.decorators import team_is_authenticated, check_registration
from isucon.portal.authentication.notify import notify_registration


class LoginView(DjangoLoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_team_limited"] = Team.objects.count() >= settings.MAX_TEAM_NUM
        return context


@check_registration
@login_required
def create_team(request):

    if Team.objects.count() >= settings.MAX_TEAM_NUM:
        return render(request, "create_team_max.html")

    user = request.user
    initial = {
        "email": user.email,
    }
    form = TeamRegisterForm(request.POST or None, request.FILES or None, user=user, initial=initial)
    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "create_team.html", {'form': form, 'username': request.user, 'email': request.user.email})

    form.save()

    try:
        notify_registration()
    except:
        pass

    return redirect("team_settings")

@check_registration
@login_required
def join_team(request):
    user = request.user
    initial = {}
    form = JoinToTeamForm(request.POST or None, request.FILES or None, user=user, initial=initial)

    if not form.is_valid():
        # フォームの内容が不正なら戻す
        return render(request, "join_team.html", {'form': form, 'username': request.user})

    form.save()

    try:
        notify_registration()
    except:
        pass

    return redirect("team_settings")

def team_list(request):
    teams = Team.objects.order_by("id").prefetch_related("user_set")
    context = {"teams": teams}

    return render(request, "team_list.html", context)

def team_list_csv(request):
    teams = Team.objects.order_by("id").prefetch_related("user_set")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teams.csv"'
    writer = csv.writer(response)

    for team in teams:
        row = [team.name]
        for u in team.user_set.all():
            row.append(u.display_name)
        writer.writerow(row)

    return response
