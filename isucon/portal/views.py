from django.shortcuts import render

from isucon.portal.authentication.decorators import is_registration_available

def index(request):
    return render(request, "landing.html", {'is_registration_available': is_registration_available()})
