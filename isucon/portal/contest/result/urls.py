from django.contrib import admin
from django.urls import path, include

from isucon.portal.contest.result import views

urlpatterns = [
    path('', views.dashboard, name="result_dashboard"),
    path('scores/', views.scores, name="result_scores"),
    path('jobs/', views.jobs, name="result_jobs"),
    path('jobs/<int:pk>/', views.job_detail, name="result_job_detail"),
]
