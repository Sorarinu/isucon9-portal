from django.shortcuts import redirect
from django.http import HttpResponseRedirect

def team_is_now_on_contest(function):
    def _function(request,*args, **kwargs):
        # TODO: コンテスト実施中かどうかを確認する
        if True:
            return redirect("team_information")
        return function(request, *args, **kwargs)
    return _function
