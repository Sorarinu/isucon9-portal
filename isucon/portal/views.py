from django.conf import settings
from django.shortcuts import render

from isucon.portal.authentication.decorators import is_registration_available

def index(request):
    context = {
        'is_registration_available': is_registration_available(),
        'registration_start_at': settings.REGISTRATION_START_AT,
        'registration_end_at': settings.REGISTRATION_END_AT,
    }
    return render(request, "landing.html", context)
