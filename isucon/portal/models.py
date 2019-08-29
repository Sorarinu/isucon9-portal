import dateutil.parser

from django.db import models


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


class LogicalDeleteMixin:
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)
    deleted_at = models.DateTimeField("削除日時", blank=True, null=True)
