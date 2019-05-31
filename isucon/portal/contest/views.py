from django.shortcuts import render

from isucon.portal.authentication.decorators import team_is_authenticated

def index(request):
    return render(request, "index.html")

@team_is_authenticated
def dashboard(request):
    return render(request, "dashboard.html")

@team_is_authenticated
def jobs(request):
    return render(request, "jobs.html")

@team_is_authenticated
def scores(request):
    return render(request, "scores.html")

@team_is_authenticated
def servers(request):
    return render(request, "servers.html")
