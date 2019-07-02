import functools

from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

def has_team(user):
    return user.is_authenticated and user.team is not None

team_is_authenticated = user_passes_test(has_team)

def is_registration_available():
    """登録可能か日時チェック"""
    now = timezone.now()
    return settings.REGISTRATION_START_AT <= now <= settings.REGISTRATION_END_AT

def check_registration(function):
    @functools.wraps(function)
    def _function(request, *args, **kwargs):
        if not is_registration_available():
            return redirect("index")
        return function(request, *args, **kwargs)
    return _function
