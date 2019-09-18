from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.conf import settings

def team_is_now_on_contest(function):
    """チームにとってコンテスト開催中かチェックするデコレータを返す"""
    def _function(request, *args, **kwargs):
        team = request.user.team
        if not team.is_playing() and not request.user.is_staff:
            # 開催日でなければ、チーム情報ページに飛ばす
            return redirect("team_settings")
        return function(request, *args, **kwargs)
    return _function


def show_result_enabled(function):
    """結果表示有効かどうか"""
    def _function(request, *args, **kwargs):
        if settings.SHOW_RESULT_AFTER > timezone.now():
            # 開催日でなければ、チーム情報ページに飛ばす
            return redirect("team_settings")
        return function(request, *args, **kwargs)
    return _function
