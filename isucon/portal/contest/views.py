from django.shortcuts import render

def index(request):
    return render(request, "index.html")


def dashboard(request):
    return render(request, "dashboard.html")

def jobs(request):
    return render(request, "jobs.html")

def scores(request):
    return render(request, "scores.html")
