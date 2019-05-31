from django.db import models

from isucon.portal.models import LogicalDeleteMixin
from isucon.portal.authentication.models import Team


class ScoreHistory(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "スコア履歴"

    team = models.ForeignKey(Team, verbose_name="チーム", on_delete=models.PROTECT)
    score = models.IntegerField("得点")