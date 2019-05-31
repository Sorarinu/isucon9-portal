from django.contrib import admin
from django.urls import path

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name="login.html")),
    path('logout/', auth_views.LogoutView.as_view(template_name="logout.html")),
]
