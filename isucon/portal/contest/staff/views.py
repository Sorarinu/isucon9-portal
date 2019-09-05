import datetime
from dateutil.parser import parse as parse_datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseNotAllowed, HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

from isucon.portal.contest.models import Server, Job, Score
from isucon.portal.redis.client import RedisClient

def get_base_context(user):
    return {
        "staff": True,
    }

def get_participate_at(request):
    if request.session.has_key('participate_at'):
        participate_at_str = request.session.get('participate_at', '')
    else:
        participate_at_str = request.GET.get('participate_at', '')

    try:
        participate_at = parse_datetime(participate_at_str).date()
    except ValueError:
        participate_at = datetime.date.today()

    request.session['participate_at'] = participate_at_str

    return participate_at

@staff_member_required
def dashboard(request):
    context = get_base_context(request.user)
    participate_at = get_participate_at(request)

    try:
        top_n = int(request.GET.get("graph_teams", settings.RANKING_TOPN))
    except ValueError:
        top_n = settings.RANKING_TOPN

    top_teams = Score.objects.passed().filter(team__participate_at=participate_at)[:30]

    # topN チームID配列を用意
    ranking = [row["team__id"] for row in
                Score.objects.passed().filter(team__participate_at=participate_at).values("team__id")[:top_n]]

    # キャッシュ済みグラフデータの取得 (topNのみ表示するデータ)
    client = RedisClient()
    graph_labels, graph_datasets = client.get_graph_data_for_staff(participate_at, ranking)

    context.update({
        "top_teams": top_teams,
        "graph_labels": graph_labels,
        "graph_datasets": graph_datasets,
    })

    return render(request, "staff/dashboard.html", context)



@staff_member_required
def scores(request):
    context = get_base_context(request.user)
    participate_at = get_participate_at(request)

    context.update({
        "passed": Score.objects.passed().filter(team__participate_at=participate_at),
        "failed": Score.objects.failed().filter(team__participate_at=participate_at),
    })

    return render(request, "scores.html", context)


@staff_member_required
def jobs(request):
    context = get_base_context(request.user)
    participate_at = get_participate_at(request)

    jobs = Job.objects.of_team(request.user.team)
    context.update({
        "jobs": jobs,
    })

    return render(request, "staff/jobs.html", context)


@staff_member_required
def job_detail(request, pk):
    context = get_base_context(request.user)
    participate_at = get_participate_at(request)

    job = get_object_or_404(Job, pk=pk)
    context.update({
        "job": job,
    })

    return render(request, "staff/job_detail.html", context)
