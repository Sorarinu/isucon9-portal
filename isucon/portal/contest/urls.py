from django.contrib import admin
from django.urls import path, include

from isucon.portal.contest import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('jobs/', views.jobs, name="jobs"),
    path('jobs/<int:pk>/', views.job_detail, name="job_detail"),
    path('scores/', views.scores, name="scores"),
    path('servers/', views.servers, name="servers"),
    path('servers/<int:pk>/', views.delete_server, name="delete_server"),
    path('teams/', views.teams, name="teams"),
    path('settings/team/', views.team_settings, name="team_settings"),
    path('settings/icon/', views.update_user_icon, name="update_user_icon"),
]
