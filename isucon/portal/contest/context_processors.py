from django.conf import settings


def settings_url(request):
    is_now_on_contest = False
    if request.user.is_authenticated and request.user.team is not None:
        is_now_on_contest = request.user.team.is_playing()

    context = {
        'discord_url': settings.DISCORD_URL,
        'manual_url': settings.MANUAL_URL,
        'isucon_official_url': settings.ISUCON_OFFICIAL_URL,
        'regulation_url': settings.REGULATION_URL,
        'twitter_url': settings.TWITTER_URL,
        'term_url': settings.TERM_URL,
        'is_now_on_contest': is_now_on_contest,
    }
    return context
