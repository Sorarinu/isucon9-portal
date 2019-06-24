from django.contrib import admin

from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, Job


class ServerAdmin(admin.ModelAdmin):
    list_display = ["id", "hostname", "global_ip", "private_ip"]
    list_filter = ["hostname"]

admin.site.register(Server, ServerAdmin)


class BenchmarkerAdmin(admin.ModelAdmin):
    list_display = ["id", "ip"]
    list_filter = ["ip"]

admin.site.register(Benchmarker, BenchmarkerAdmin)


class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "score"]
    list_filter = ["team"]

admin.site.register(ScoreHistory, ScoreHistoryAdmin)


class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "status", "is_passed", "score", "result_json", "log_text"]
    list_filter = ["team", "status", "is_passed"]

admin.site.register(Job, JobAdmin)