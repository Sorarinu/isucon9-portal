import json

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
    bench_queue = models.ForeignKey('contest.BenchQueue', verbose_name="ベンチキュー", on_delete=models.PROTECT, null=True)
    score = models.IntegerField("得点")
    is_passed = models.BooleanField("正答フラグ", default=False)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = ScoreHistoryManager()

class BenchQueueManager(models.Manager):

    def enqueue(self):
        pass

    def dequeue(self):
        pass

    def cancel(self):
        pass

    def abort(self):
        pass


class BenchQueue(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ベンチキュー"

    # 進捗の選択肢
    PROGRESS_CHOICES = (
        ('waiting', 'waiting'), # 処理待ち
        ('running', 'running'), # 処理中
        ('done', 'done'), # 処理完了
        ('aborted', 'aborted'), # 異常終了
        ('canceled', 'canceled'), # 意図的なキャンセル
    )

    # 結果の選択肢
    RESULT_CHOICES = (
        ('unknown', 'unknown'), # 不明
        ('success', 'success'), # 成功
        ('fail', 'fail'), # 失敗
    )

    node = models.CharField("ノード", max_length=100)

    # ターゲット情報
    target_hostname = models.CharField("対象ホスト名", max_length=100)
    target_ip = models.CharField("対象IPアドレス", max_length=100)

    # Choice系
    progress = models.IntegerField("進捗", choices=PROGRESS_CHOICES, default=1)
    result = models.IntegerField("結果", choices=RESULT_CHOICES, default=1)

    score = models.IntegerField("獲得スコア", default=0, null=False)

    # ベタテキスト
    result_raw = models.TextField("結果JSON")
    log_raw = models.TextField("ログ文字列")

    objects = BenchQueueManager()

    @property
    def is_finished(self):
        return self.result in ['done', 'aborted', 'canceled']

    @property
    def result_json(self):
        return json.loads(self.result_raw)

