import locale
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.conf import settings
from stdimage.models import StdImageField

from isucon.portal.models import LogicalDeleteMixin

locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')

class User(AbstractUser):
    team = models.ForeignKey("Team", blank=True, null=True, on_delete=models.SET_NULL)
    icon = StdImageField(upload_to='icons/', blank=True, null=True, variations={
        'thumbnail': (150, 150, True),
    })
    is_student = models.BooleanField('学生フラグ', default=False, blank=True)
    display_name = models.CharField('表示名', max_length=100)

    def __str__(self):
        return self.display_name

class Team(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "チーム"

    PARTICIPATE_AT_CHOICES = [(d, "{}日目 ({})".format(idx+1, d.strftime("%Y-%m-%d %a"))) for idx, d in enumerate(settings.CONTEST_DATES)]

    owner = models.OneToOneField(User, verbose_name="オーナー", on_delete=models.PROTECT, related_name="+")
    is_active = models.BooleanField("有効", default=True, blank=True)
    name = models.CharField("名前", max_length=100, unique=True)
    password = models.CharField("パスワード", max_length=100, unique=True)

    benchmarker = models.ForeignKey('contest.Benchmarker', verbose_name="ベンチマーカー", on_delete=models.SET_NULL, null=True, blank=True)

    participate_at = models.DateField("参加日", blank=True)

    # ベンチマーク結果に関連する情報(チームと一蓮托生なのでCASCADE)
    aggregated_score = models.ForeignKey('contest.AggregatedScore', on_delete=models.CASCADE, null=True, blank=True)

    def is_playing(self):
        """参加中か(日付が一致し、時刻が範囲内なら)"""
        now = timezone.now()
        in_date = now.date() == self.participate_at
        in_time = settings.CONTEST_START_TIME <= now.time() <= settings.CONTEST_END_TIME
        return in_date and in_time

    def __str__(self):
        return self.name

    @property
    def score(self):
        # FIXME: this is a dummy
        return {
            "latest_score": 100,
            "best_score": 2000,
            "latest_status": "Dummy",
            "updated_at": timezone.now(),
        }
