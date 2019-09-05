from django.contrib import admin
from django.urls import path, include

from isucon.portal.contest.staff import views

urlpatterns = [
    path('', views.dashboard, name="staff_dashboard"),
    path('scores/', views.scores, name="staff_scores"),
    path('jobs/', views.jobs, name="staff_jobs"),
    path('jobs/<int:pk>/', views.job_detail, name="staff_job_detail"),
]
