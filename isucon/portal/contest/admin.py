from django.contrib import admin

from isucon.portal.contest.models import Server, Benchmarker, ScoreHistory, BenchQueue


class ServerAdmin(admin.ModelAdmin):
    list_display = ["id", "hostname", "global_ip", "private_ip", "private_network"]
    list_filter = ["hostname"]

admin.site.register(Server, ServerAdmin)


class BenchmarkerAdmin(admin.ModelAdmin):
    list_display = ["id", "network", "node"]
    list_filter = ["node"]

admin.site.register(Benchmarker, BenchmarkerAdmin)


class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "score"]
    list_filter = ["team"]

admin.site.register(ScoreHistory, ScoreHistoryAdmin)


class BenchQueueAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "node", "target_hostname", "target_ip", "status", "is_passed", "score", "result_json", "log_text"]
    list_filter = ["team", "target_hostname", "target_ip", "status", "is_passed"]

admin.site.register(BenchQueue, BenchQueueAdmin)