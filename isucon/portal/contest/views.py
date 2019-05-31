from django.shortcuts import render, get_object_or_404

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
def job_detail(request, pk):

    # FIXME: Query
    # job = get_object_or_404(Job.objcets.filter(team=user.team), pk=pk)
    job = {
        "id": pk,
        "state": "dummy",
    } # Dummy

    context = get_base_context(request.user)

    context.update({
        "job": job,
    })
    return render(request, "job_detail.html", context)




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
