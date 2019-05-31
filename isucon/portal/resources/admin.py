from django.contrib import admin

from isucon.portal.resources.models import Server, Benchmarker

class ServerAdmin(admin.ModelAdmin):
    list_display = ["id", "hostname", "global_ip", "private_ip", "private_network", "benchmarker"]
    list_filter = ["hostname"]

admin.site.register(Server, ServerAdmin)


class BenchmarkerAdmin(admin.ModelAdmin):
    list_display = ["id", "network", "node"]
    list_filter = ["node"]

admin.site.register(Benchmarker, BenchmarkerAdmin)