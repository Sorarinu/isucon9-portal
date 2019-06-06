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

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT)
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

    def enqueue(self, team):
        # 重複チェック
        if self.is_duplicated(team):
            return

        # チームからサーバやベンチマーカを得る
        try:
            # FIXME: 実際に何台になるかまだわからんけど、１台を仮定
            server = Server.objects.get(team=team)
        except Server.DoesNotExist:
            return
        benchmarker = team.benchmarker

        # 追加
        job = self.model(
            team=team,
            target_hostname=server.hostname,
            target_ip=server.global_ip, # FIXME: あってるか確認
            node=benchmarker.node,
        )
        job.save(using=self._db)

        return job.id

    def dequeue(self, hostname):
        job = self.get_queryset().filter(target_hostname=hostname, progress="waiting")[0]

        # FIXME: ホストの負荷を考慮

        # 状態を処理中にする
        job.progress = "running"
        job.save(using=self._db)

        return job

    def done(self, job_id, result_raw, log_raw):
        # FIXME: team_id を取ってきて、存在チェック

        # ベンチの更新
        try:
            job = self.get_queryset().get(pk=job_id)
        except BenchQueue.DoesNotExist:
            return
        job.progress = BenchQueue.DONE
        job.result_raw = result_raw
        job.log_raw = log_raw

        result_json = job.result_json
        job.score = result_json['score']
        if result_json['pass']:
            job.result = BenchQueue.SUCCESS
        else:
            job.result = BenchQueue.FAIL

        job.save(using=self._db)

        # FIXME: スコア履歴更新

    def abort(self, job_id, result_raw, log_raw):
        job = self.get_queryset().get(pk=job_id)
        job.progress = BenchQueue.ABORTED
        job.result_raw = result_raw
        job.log_raw = log_raw
        job.save(using=self._db)

    def abort_timeout(self):
        # TODO: 実装
        pass

    def is_duplicated(self, team):
        """重複enqueue防止"""
        jobs = self.get_queryset().filter(team=team, progress__in=[
            BenchQueue.WAITING,
            BenchQueue.RUNNING,
        ])
        return len(jobs) > 0


class BenchQueue(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "ベンチキュー"
        ordering=('-created_at',)

    # 進捗の選択肢
    WAITING = 'waiting'
    RUNNING = 'running'
    DONE = 'done'
    ABORTED = 'aborted'
    CANCELED = 'canceled'
    PROGRESS_CHOICES = (
        (WAITING, WAITING), # 処理待ち
        (RUNNING, RUNNING), # 処理中
        (DONE, DONE), # 処理完了
        (ABORTED, ABORTED), # 異常終了
        (CANCELED, CANCELED), # 意図的なキャンセル
    )

    # 結果の選択肢
    UNKNOWN = 'unknown'
    SUCCESS = 'success'
    FAIL = 'fail'
    RESULT_CHOICES = (
        (UNKNOWN, UNKNOWN), # 不明
        (SUCCESS, SUCCESS), # 成功
        (FAIL, FAIL), # 失敗
    )

    # FIXME: SET_NULLされたレコードを、ジョブ取得時に考慮
    team = models.ForeignKey('authentication.Team', verbose_name="チーム", null=True, on_delete=models.SET_NULL)
    node = models.CharField("ノード", max_length=100)

    # ターゲット情報
    target_hostname = models.CharField("対象ホスト名", max_length=100)
    target_ip = models.CharField("対象IPアドレス", max_length=100)

    # Choice系
    progress = models.CharField("進捗", max_length=100, choices=PROGRESS_CHOICES, default=WAITING)
    result = models.CharField("結果", max_length=100, choices=RESULT_CHOICES, default=1)

    score = models.IntegerField("獲得スコア", default=0, null=False)

    # ベタテキスト
    result_raw = models.TextField("結果JSON")
    log_raw = models.TextField("ログ文字列")

    # 日時
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = BenchQueueManager()

    @property
    def is_finished(self):
        return self.result in [
            self.DONE,
            self.ABORTED,
            self.CANCELED,
        ]

    @property
    def result_json(self):
        return json.loads(self.result_raw)

    def append_log(self, log):
        self.log_raw += log
        self.save(update_fields=["log_raw"])

