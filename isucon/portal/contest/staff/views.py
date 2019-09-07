import datetime
from dateutil.parser import parse as parse_datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseNotAllowed, HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from isucon.portal.contest.models import Server, Job, Score
from isucon.portal.redis.client import RedisClient
from isucon.portal import utils as portal_utils

def get_base_context(user):
    return {
        "staff": True,
    }

def get_participate_at(request):
    if 'participate_at' in request.GET:
        participate_at_str = request.GET.get('participate_at', '')
    else:
        participate_at_str = request.session.get('participate_at', '')

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

    # NOTE: team.participate_at の日付の、CONTEST_START_TIME-10minutes ~ CONTEST_END_TIME+10minutes にするようにmin, maxを渡す
    graph_start_at = datetime.datetime.combine(participate_at, settings.CONTEST_START_TIME) - datetime.timedelta(minutes=10)
    graph_start_at = graph_start_at.replace(tzinfo=portal_utils.jst)

    graph_end_at = datetime.datetime.combine(participate_at, settings.CONTEST_END_TIME) + datetime.timedelta(minutes=10)
    graph_end_at = graph_end_at.replace(tzinfo=portal_utils.jst)

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
        "graph_min_label": portal_utils.normalize_for_graph_label(graph_start_at),
        "graph_max_label": portal_utils.normalize_for_graph_label(graph_end_at),
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

    return render(request, "staff/scores.html", context)


@staff_member_required
def jobs(request):
    context = get_base_context(request.user)
    participate_at = get_participate_at(request)

    def paginate_query(request, queryset, count):
        paginator = Paginator(queryset, count)
        page = request.GET.get('page', "1")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginatot.page(paginator.num_pages)

        return page_obj

    page = paginate_query(request, Job.objects.order_by("-id"), 50)

    context.update({
        "jobs": page,
        "page_obj": page,
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
