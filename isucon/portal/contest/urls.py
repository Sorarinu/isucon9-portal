from django.contrib import admin
from django.urls import path, include

from isucon.portal.contest import views

urlpatterns = [
    path('', views.index),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('jobs/', views.jobs, name="jobs"),
    path('scores/', views.scores, name="scores"),
    path('servers/', views.servers, name="servers"),
]
