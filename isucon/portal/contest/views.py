from django.shortcuts import render, get_object_or_404

from isucon.portal.authentication.decorators import team_is_authenticated
from isucon.portal.contest.models import Server, ScoreHistory, Job

def index(request):
    return render(request, "index.html")


def get_base_context(user):
    target_server = Server.objects.get_bench_target(user.team)
    # FIXME: ラストスパート判定
    # ラスト１時間であるかを判定すれば良いので、競技の開始、終了時刻をsettings.pyなどに突っ込んでおく
    # https://github.com/isucon/isucon8-final/blob/d1480128c917f3fe4d87cb84c83fa2a34ca58d39/portal/lib/ISUCON8/Portal/Web.pm#L92
    is_last_spurt = False

    return {
        "target_server": target_server,
        "is_last_spurt": is_last_spurt,
    }

@team_is_authenticated
def dashboard(request):
    context = get_base_context(request.user)

    recent_jobs = Job.objects.of_team(team=request.user.team).order_by("-created_at")[10]
    top_teams = ScoreHistory.objects.get_top_teams()
    context.update({
        "recent_jobs": recent_jobs,
        "top_teams": top_teams,
    })

    return render(request, "dashboard.html", context)

@team_is_authenticated
def jobs(request):
    context = get_base_context(request.user)

    jobs = Job.objects.of_team(request.user.team)
    context.update({
        "jobs": jobs,
    })

    return render(request, "jobs.html", context)

@team_is_authenticated
def job_detail(request, pk):
    context = get_base_context(request.user)

    job = get_object_or_404(Job.objects.filter(team=request.user.team), pk=pk)
    context.update({
        "job": job,
    })

    return render(request, "job_detail.html", context)

@team_is_authenticated
def scores(request):
    context = get_base_context(request.user)

    teams = ScoreHistory.objects.get_top_teams()
    context.update({
        "teams": teams,
    })

    return render(request, "scores.html", context)

@team_is_authenticated
def servers(request):
    context = get_base_context(request.user)

    servers = Server.objects.of_team(request.user.team)

    context.update({
        "servers": servers,
    })
    return render(request, "servers.html", context)
