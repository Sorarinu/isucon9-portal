import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser

from isucon.portal.models import LogicalDeleteMixin
from isucon.portal.resources.models import Benchmarker

class User(AbstractUser):
    team = models.ForeignKey("Team", blank=True, null=True, on_delete=models.PROTECT)

class Team(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "チーム"

    owner = models.OneToOneField(User, verbose_name="オーナー", on_delete=models.PROTECT, related_name="+")
    is_active = models.BooleanField("有効", default=True, blank=True)
    name = models.CharField("名前", max_length=100, unique=True)
    password = models.CharField("パスワード", max_length=100, unique=True)

    benchmarker = models.ForeignKey(Benchmarker, verbose_name="ベンチマーカー", blank=True, null=True, on_delete=models.SET_NULL)

    def __name__(self):
        return self.name

    @property
    def score(self):
        # FIXME: this is a dummy
        return {
            "latest_score": 100,
            "best_score": 2000,
            "latest_status": "Dummy",
            "updated_at": datetime.datetime.now()
        }
