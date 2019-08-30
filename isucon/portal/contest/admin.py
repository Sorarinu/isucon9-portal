import dateutil.parser

from django.contrib import admin
from django.conf import settings
from django import forms

from isucon.portal.contest.models import (
    Server,
    Information,
    Benchmarker,
    Score,
    Job
)


class ServerAdmin(admin.ModelAdmin):
    list_display = ["id", "hostname", "global_ip", "private_ip"]
    list_filter = ["hostname"]

admin.site.register(Server, ServerAdmin)


class InformationAdminForm(forms.ModelForm):
    class Meta:
        model = Information
        fields = ["id", "is_enabled", "allowed_participate_at", "title", "description"]


    PARTICIPATE_AT_CHOICES = [(d, "{}日目 ({})".format(idx+1, d.strftime("%Y-%m-%d %a"))) for idx, d in enumerate(settings.CONTEST_DATES)]


    allowed_participate_at = forms.TypedMultipleChoiceField(
        label="共有対象参加日",
        widget=forms.CheckboxSelectMultiple(choices=PARTICIPATE_AT_CHOICES),
        required=False,
        choices=PARTICIPATE_AT_CHOICES,
        coerce=lambda x: dateutil.parser.parse(x).date(),
    )

    def clean_allowed_participate_at(self):
        v = self.cleaned_data["allowed_participate_at"]
        return v



class InformationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "is_enabled", "allowed_participate_at"]
    list_filter = ["is_enabled"]
    form = InformationAdminForm

admin.site.register(Information, InformationAdmin)


class BenchmarkerAdmin(admin.ModelAdmin):
    list_display = ["id", "ip"]
    list_filter = ["ip"]

admin.site.register(Benchmarker, BenchmarkerAdmin)


class ScoreAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "best_score", "latest_score", "latest_is_passed"]
    list_filter = ["latest_is_passed"]

admin.site.register(Score, ScoreAdmin)

class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "status", "is_passed", "score", "stdout", "stderr"]
    list_filter = ["team", "status", "is_passed"]

admin.site.register(Job, JobAdmin)
