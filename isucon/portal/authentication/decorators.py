from django.contrib.auth.decorators import user_passes_test

def has_team(user):
    return user.is_authenticated and user.team is not None

team_is_authenticated = user_passes_test(has_team)

def is_contest_is_available(user):
    team = user.team
    return team.is_playing()

check_contest_is_available = user_passes_test(is_contest_is_available)