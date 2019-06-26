import functools

from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

def has_team(user):
    return user.is_authenticated and user.team is not None

team_is_authenticated = user_passes_test(has_team)

def check_registration(function):
    """登録可能か日時チェック"""
    @functools.wraps(function)
    def _function(request, *args, **kwargs):
        now = timezone.now().now()
        if not (settings.REGISTRATION_START_AT <= now <= settings.REGISTRATION_END_AT):
            return redirect("/")
        return function(request, *args, **kwargs)
    return _function
