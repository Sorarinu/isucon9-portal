from django.contrib import admin

from isucon.portal.contest.models import (
    Server,
    Information,
    Benchmarker,
    ScoreHistory,
    Job
)


class ServerAdmin(admin.ModelAdmin):
    list_display = ["id", "hostname", "global_ip", "private_ip"]
    list_filter = ["hostname"]

admin.site.register(Server, ServerAdmin)


class InformationAdmin(admin.ModelAdmin):
    list_display = ["id", "description"]
    list_filter = ["description"]

admin.site.register(Information, InformationAdmin)


class BenchmarkerAdmin(admin.ModelAdmin):
    list_display = ["id", "ip"]
    list_filter = ["ip"]

admin.site.register(Benchmarker, BenchmarkerAdmin)


class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "score"]
    list_filter = ["team"]

admin.site.register(ScoreHistory, ScoreHistoryAdmin)


class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "status", "is_passed", "score", "result_json", "stdout", "stderr"]
    list_filter = ["team", "status", "is_passed"]

admin.site.register(Job, JobAdmin)