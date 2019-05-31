from django.contrib import admin
from django.urls import path, include

from isucon.portal.contest import views

urlpatterns = [
    path('', views.index),
]
