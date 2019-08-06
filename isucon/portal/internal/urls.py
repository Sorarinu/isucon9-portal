from django.urls import path, include

from isucon.portal.internal import views


urlpatterns = [
    path('', include(views.router.urls)),
]