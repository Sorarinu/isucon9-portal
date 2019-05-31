from django.db import models
from django.contrib.auth.models import AbstractUser

from isucon.portal.models import LogicalDeleteMixin

class User(AbstractUser):
    pass

class Team(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "チーム"

    owner = models.OneToOneField(User, verbose_name="オーナー", on_delete=models.PROTECT)
    is_active = models.BooleanField("有効", default=True, blank=True)
    name = models.CharField("名前", max_length=100, unique=True)
    password = models.CharField("パスワード", max_length=100, unique=True)

    benchmarker = models.ForeignKey('contest.Benchmarker', verbose_name="ベンチマーカー", on_delete=models.PROTECT, null=True)

    def __name__(self):
        return self.name
