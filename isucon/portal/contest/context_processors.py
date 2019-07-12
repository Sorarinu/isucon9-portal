from django.conf import settings


def settings_url(request):
    context = {
        'discord_url': settings.DISCORD_URL,
        'manual_url': settings.MANUAL_URL,
        'isucon_official_url': settings.ISUCON_OFFICIAL_URL,
        'regulation_url': settings.REGULATION_URL,
        'twitter_url': settings.TWITTER_URL,
        'term_url': settings.TERM_URL,
    }
    return context
