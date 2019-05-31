from django.shortcuts import render

from isucon.portal.authentication.decorators import team_is_authenticated

def index(request):
    return render(request, "index.html")


def get_base_context(user):
    # FIXME: Dummy
    target_server = None
    is_last_spurt = False

    return {
        "target_server": target_server,
        "is_last_spurt": is_last_spurt,
    }

@team_is_authenticated
def dashboard(request):
    context = get_base_context(request.user)

    # FIXME: Query
    recent_jobs = []
    top_teams = []

    context.update({
        "recent_jobs": recent_jobs,
        "top_teams": top_teams,
    })
    return render(request, "dashboard.html", context)

@team_is_authenticated
def jobs(request):
    context = get_base_context(request.user)

    # FIXME: Query
    jobs = []

    context.update({
        "jobs": jobs,
    })
    return render(request, "jobs.html", context)

@team_is_authenticated
def scores(request):
    context = get_base_context(request.user)

    # FIXME: Query
    teams = []

    context.update({
        "teams": teams,
    })
    return render(request, "scores.html", context)

@team_is_authenticated
def servers(request):
    context = get_base_context(request.user)

    # FIXME: Query
    servers = []

    context.update({
        "servers": servers,
    })
    return render(request, "servers.html", context)
