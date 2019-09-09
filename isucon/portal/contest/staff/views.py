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
from isucon.portal.contest.redis.client import RedisClient
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
        participate_at_str = participate_at.strftime('%Y-%m-%d')

    request.session['participate_at'] = participate_at_str

    return participate_at, participate_at_str

@staff_member_required
def dashboard(request):
    context = get_base_context(request.user)
    participate_at, participate_at_str = get_participate_at(request)

    try:
        top_n = int(request.GET.get("graph_teams", settings.RANKING_TOPN))
    except ValueError:
        top_n = settings.RANKING_TOPN

    top_teams = Score.objects.passed().filter(team__participate_at=participate_at)[:30]

    context.update({
        "top_teams": top_teams,
        "graph_participate_at": participate_at_str,
        "graph_topn": top_n
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

    show_pages = []
    for n in page.paginator.page_range:
        if n <= 3 or (page.paginator.num_pages-3) < n:
            show_pages.append(n)
        elif page.number - 2 < n < page.number + 2:
            show_pages.append(n)
        elif n == 4:
            show_pages.append(None)
        elif page.number - 2 == n or n == page.number + 2:
            if show_pages[-1]:
                show_pages.append(None)

    context.update({
        "jobs": page,
        "page_obj": page,
        "show_pages": show_pages,
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

@staff_member_required
def graph(request):
    if not request.is_ajax():
        return HttpResponse("このエンドポイントはAjax専用です", status=400)

    # participate_at, top_n は dashboardにより必ず何かしらの値が設定される
    participate_at = parse_datetime(request.GET.get("participate_at")).date()
    top_n = int(request.GET.get("top_n"))

    team = request.user.team

    ranking = [row["team__id"] for row in
                    Score.objects.passed().filter(team__participate_at=team.participate_at).values("team__id")[:top_n]]

    client = RedisClient()
    graph_datasets, graph_min, graph_max = client.get_graph_data_for_staff(participate_at, ranking)

    data = {
        'graph_datasets': graph_datasets,
        'graph_min': graph_min,
        'graph_max': graph_max,
    }

    return JsonResponse(
        data, status = 200
    )


