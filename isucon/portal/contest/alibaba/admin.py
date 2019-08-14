import dateutil.parser

from django import forms
from django.contrib import admin
from django.conf import settings

from isucon.portal.authentication.models import Team
from isucon.portal.contest.alibaba.models import Image


class ImageAdminForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["id", "name", "is_enabled", "allowed_participate_at"]


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


class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "is_enabled", "allowed_participate_at"]
    list_filter = ["is_enabled"]
    form = ImageAdminForm

admin.site.register(Image, ImageAdmin)
