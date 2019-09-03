from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseNotAllowed, HttpResponse, JsonResponse
from django.utils import timezone

from isucon.portal.authentication.decorators import team_is_authenticated
from isucon.portal.authentication.models import Team
from isucon.portal.contest.decorators import team_is_now_on_contest
from isucon.portal.contest.models import Server, Job, Score

from isucon.portal.contest.forms import TeamForm, UserForm, ServerTargetForm, UserIconForm, ServerAddForm
from isucon.portal.redis.client import RedisClient


def get_base_context(user):
    try:
        target_server = Server.objects.get_bench_target(user.team)
    except Server.DoesNotExist:
        # FIXME: チーム作成直後、チームのサーバは存在しないため、ここでDoesNotExistが投げられるのを回避するためのコード
        # チームにサーバを割り当てる時どうするか決める
        target_server = None
    # FIXME: ラストスパート判定
    # ラスト１時間であるかを判定すれば良いので、競技の開始、終了時刻をsettings.pyなどに突っ込んでおく
    # https://github.com/isucon/isucon8-final/blob/d1480128c917f3fe4d87cb84c83fa2a34ca58d39/portal/lib/ISUCON9/Portal/Web.pm#L92
    is_last_spurt = False

    return {
        "target_server": target_server,
        "is_last_spurt": is_last_spurt,
    }
@team_is_authenticated
@team_is_now_on_contest
def dashboard(request):
    context = get_base_context(request.user)

    recent_jobs = Job.objects.of_team(team=request.user.team).order_by("-created_at")[:10]
    top_teams = Score.objects.passed().filter(team__participate_at=request.user.team.participate_at)[:30]

    # キャッシュ済みグラフデータの取得
    client = RedisClient()
    team_cnt = Team.objects.filter(participate_at=request.user.team.participate_at).count()
    topn = min(settings.RANKING_TOPN, team_cnt)
    graph_datasets = client.get_graph_data(request.user.team, topn=topn)

    context.update({
        "recent_jobs": recent_jobs,
        "top_teams": top_teams,
        "graph_datasets": graph_datasets,
    })

    return render(request, "dashboard.html", context)

@team_is_authenticated
@team_is_now_on_contest
def jobs(request):
    context = get_base_context(request.user)

    jobs = Job.objects.of_team(request.user.team)
    context.update({
        "jobs": jobs,
    })

    return render(request, "jobs.html", context)

@team_is_authenticated
@team_is_now_on_contest
def job_detail(request, pk):
    context = get_base_context(request.user)

    job = get_object_or_404(Job.objects.filter(team=request.user.team), pk=pk)
    context.update({
        "job": job,
    })

    return render(request, "job_detail.html", context)

@team_is_authenticated
@team_is_now_on_contest
def job_enqueue(request):

    if not request.is_ajax():
        return HttpResponse("このエンドポイントはAjax専用です", status=400)

    context = get_base_context(request.user)
    job = None
    try:
        job = Job.objects.enqueue(request.user.team)
    except Job.DuplicateJobError:
        return JsonResponse(
            {"error": "実行中のジョブがあります"}, status = 409
        )

    data = {
        "id": job.id,
    }

    return JsonResponse(
        data, status = 200
    )


@team_is_authenticated
@team_is_now_on_contest
def scores(request):
    context = get_base_context(request.user)

    context.update({
        "passed": Score.objects.passed().filter(team__participate_at=request.user.team.participate_at),
        "failed": Score.objects.failed().filter(team__participate_at=request.user.team.participate_at),
    })

    return render(request, "scores.html", context)

@team_is_authenticated
@team_is_now_on_contest
def servers(request):
    context = get_base_context(request.user)
    servers = Server.objects.of_team(request.user.team)
    add_form = ServerAddForm(team=request.user.team)

    if request.method == "POST":
        action = request.POST.get("action", "").lower()

        if action == "target":
            form = ServerTargetForm(request.POST, team=request.user.team)
            if form.is_valid():
                server = form.save()
                if Server.objects.of_team(request.user.team).count() == 1:
                    Server.objects.of_team(request.user.team).update(is_bench_target=True)
                messages.success(request, "ベンチマーク対象のサーバを変更しました")
                return redirect("servers")

        if action == "add":
            add_form = ServerAddForm(request.POST, team=request.user.team)
            if add_form.is_valid():
                add_form.save()
                messages.success(request, "サーバを追加しました")
                return redirect("servers")

    context.update({
        "servers": servers,
        "add_form": add_form
    })
    return render(request, "servers.html", context)


@team_is_authenticated
@team_is_now_on_contest
def delete_server(request, pk):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    server = get_object_or_404(Server.objects.of_team(request.user.team), pk=pk)

    if server.is_bench_target:
        messages.warning(request, "ベンチマーク対象のサーバは削除できません")
        if request.is_ajax():
            return HttpResponse("Error")
        return redirect("servers")

    server.delete()

    if request.is_ajax():
        return JsonResponse(
            {}, status = 200
        )

    messages.success(request, "サーバを削除しました")
    return redirect("servers")


@team_is_authenticated
@team_is_now_on_contest
def teams(request):

    teams = Team.objects.filter(participate_at=request.user.team.participate_at).order_by('id').all()

    paginator = Paginator(teams, 100)

    try:
        page_index = int(request.GET.get('page', 1))
    except ValueError:
        page_index = 1

    teams = paginator.get_page(page_index)

    context = {
        'teams': teams,
    }

    return render(request, "teams.html", context)


@team_is_authenticated
def team_settings(request):
    form = TeamForm(instance=request.user.team)
    user_form = UserForm(instance=request.user)
    if request.method == "POST" and request.POST.get("action") == "team":
        form = TeamForm(request.POST, instance=request.user.team)
        if form.is_valid():
            form.save()
            messages.success(request, "チーム情報を更新しました")
            return redirect("team_settings")

    if request.method == "POST" and request.POST.get("action") == "user":
        user_form = UserForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "ユーザー情報を更新しました")
            return redirect("team_settings")

    context = {
        "form": form,
        "user_form": user_form,
        "team_members": request.user.team.user_set.all()
    }
    return render(request, "team_settings.html", context)

@team_is_authenticated
def update_user_icon(request):
    form = UserIconForm(user=request.user)
    if request.method == "POST":
        form = UserIconForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "ユーザーのアイコンを更新しました")
        else:
            messages.warning(request, "ユーザーのアイコンを更新に失敗しました")
    else:
        return HttpResponseNotAllowed(["POST"])

    if request.is_ajax():
        return JsonResponse(
            {}, status = 200
        )
    return redirect("team_settings")
