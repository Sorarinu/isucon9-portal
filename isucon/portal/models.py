from django.db import models

class LogicalDeleteMixin:
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)
    deleted_at = models.DateTimeField("削除日時", blank=True, null=True)
