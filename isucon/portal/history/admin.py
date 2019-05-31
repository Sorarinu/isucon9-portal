from django.contrib import admin

from isucon.portal.history.models import ScoreHistory

class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "score"]
    list_filter = ["team"]

admin.site.register(ScoreHistory, ScoreHistoryAdmin)