import dateutil.parser

from django.db import models
from django import forms
from isucon.portal.models import LogicalDeleteMixin

class CommaSeparatedDateField(models.CharField):
    def from_db_value(self, value, *args):
        if not value:
            return []
        return list(map(lambda x: dateutil.parser.parse(x).date(), value.split(',')))

    def to_python(self, value):
        if isinstance(value, list):
            return value

        return self.from_db_value(value)

    def get_prep_value(self, value):
        return ','.join(map(lambda x:x.strftime("%Y-%m-%d"), value))

    def value_to_string(self, obj):
        return self.get_prep_value(self.value_from_object(obj))


class Image(LogicalDeleteMixin, models.Model):

    class Meta:
        ordering = ("id",)

    id = models.CharField("イメージID", primary_key=True, max_length=256)
    name = models.CharField("名前", max_length=512)
    is_enabled = models.BooleanField("共有有効", blank=True)
    allowed_participate_at = CommaSeparatedDateField("共有対象日", max_length=512, choices=[])
