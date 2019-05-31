from django.db import models
from django.db.models import Max

from isucon.portal.models import LogicalDeleteMixin


class Benchmarker(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ベンチマーカー"

    # FIXME: ネットワーク構成により今後変更
    ip = models.CharField("IPアドレス", max_length=100)
    network = models.CharField("ネットワークアドレス", max_length=100)

    # FIXME: これってなんのフィールドなのかまだわかってない
    node = models.CharField("ノード", max_length=100)

    def __str__(self):
        return self.ip


class Server(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "サーバ"

    # FIXME: group_id を持つモデルが複数あるが、これはGroupモデルとして定義した方が管理の都合上楽そう？
    # 検討必要そうなのでまだ定義してない
    # FIXME: パスワード、鍵認証とかにすればいい気がしたのでまだ追加してない

    hostname = models.CharField("ホスト名", max_length=100, unique=True)

    global_ip = models.CharField("グローバルIPアドレス", max_length=100, unique=True)
    private_ip = models.CharField("プライベートIPアドレス", max_length=100)
    private_network = models.CharField("プライベートネットワークアドレス", max_length=100)

    def __str__(self):
        return self.hostname


class ScoreHistoryManager(models.Manager):

    def get_queryset_by_team(self, team):
        return self.get_queryset()\
                   .filter(team=team, is_passed=True)

    def get_best_score(self, team):
        """指定チームのベストスコアを取得"""
        return self.get_queryset_by_team(team)\
                   .annotate(best_score=Max('score'))[0]

    def get_latest_score(self, team):
        """指定チームの最新スコアを取得"""
        # NOTE: orderingにより最新順に並んでいるので、LIMITで取れば良い
        return self.get_queryset_by_team(team).all()[0]


class ScoreHistory(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "スコア履歴"
        ordering = ('-created_at',)

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT, null=True)
    score = models.IntegerField("得点")
    is_passed = models.BooleanField("正答フラグ", default=False)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = ScoreHistoryManager()
