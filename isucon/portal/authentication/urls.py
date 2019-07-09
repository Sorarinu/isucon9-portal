from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from isucon.portal.authentication import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path('logout/', auth_views.LogoutView.as_view(template_name="logout.html"), name="logout"),
    path('create_team/', views.create_team, name="create_team"),
    path('join_team/', views.join_team, name="join_team"),
    path('team/', views.team_information, name="team_information"),
    path('teams/', views.team_list, name="team_list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL)
