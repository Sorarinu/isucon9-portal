from django.shortcuts import redirect
from django.http import HttpResponseRedirect

def team_is_now_on_contest(function):
    """チームにとってコンテスト開催中かチェックするデコレータを返す"""
    def _function(request, *args, **kwargs):
        team = request.user.team
        if not team.is_playing():
            # 開催日でなければ、チーム情報ページに飛ばす
            return redirect("team_information")
        return function(request, *args, **kwargs)
    return _function
