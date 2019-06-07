import datetime
import json

from django.db import models
from django.db.models import Max

from isucon.portal import settings
from isucon.portal.models import LogicalDeleteMixin
from isucon.portal.contest import exceptions


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
    # FIXME: bench_queue -> job のほうがわかりやすいか
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
            raise exceptions.DuplicateJobError

        # チームからサーバやベンチマーカを得る
        try:
            # FIXME: 実際に何台になるかまだわからんけど、１台を仮定
            server = Server.objects.get(team=team)
        except Server.DoesNotExist:
            raise exceptions.TeamServerDoesNotExistError

        benchmarker = team.benchmarker

        # 追加
        job = self.model(
            team=team,
            target_hostname=server.hostname,
            target_ip=server.private_ip, # FIXME: あってるか確認
            node=benchmarker.node,
        )
        job.save(using=self._db)

        return job.id

    def dequeue(self, hostname, max_concurrency=settings.BENCHMARK_MAX_CONCURRENCY):
        job = self.get_queryset().filter(target_hostname=hostname, status=BenchQueue.WAITING).first()
        if job is None:
            raise exceptions.JobDoesNotExistError

        # ホストの負荷を考慮
        concurrency = BenchQueue.objects.filter(status=BenchQueue.RUNNING, node=job.node).count()
        if concurrency >= max_concurrency:
            raise exceptions.JobCountReachesMaxConcurrencyError

        # 状態を処理中にする
        job.status = BenchQueue.RUNNING
        job.save(using=self._db)

        return job

    def done(self, job_id, result_json, log_text):
        # ベンチの更新
        try:
            job = self.get_queryset().get(pk=job_id)
        except BenchQueue.DoesNotExist:
            raise exceptions.JobDoesNotExistError

        job.status = BenchQueue.DONE
        job.result_json = result_json
        job.log_text = log_text # FIXME: append? そうなると逐次報告だが、どうログを投げるか話し合う

        result_json_object = job.result_json_object
        job.score = result_json_object['score']
        if result_json_object['pass']:
            job.is_passed = True

        job.save(using=self._db)

        # スコアを記録
        ScoreHistory.objects.create(
            team=job.team,
            bench_queue=job,
            score=job.score,
            is_passed=job.is_passed,
        )

    def abort(self, job_id, result_json, log_text):
        try:
            job = self.get_queryset().get(pk=job_id)
        except BenchQueue.DoesNotExist:
            raise exceptions.JobDoesNotExistError

        job.status = BenchQueue.ABORTED
        job.result_json = result_json
        job.log_text = log_text
        job.save(using=self._db)

    def abort_timeout(self, timeout_sec=settings.BENCHMARK_ABORT_TIMEOUT_SEC):
        deadline = datetime.datetime.now() - datetime.timedelta(seconds=timeout_sec)
        jobs = BenchQueue.objects.filter(status=BenchQueue.RUNNING, updated_at__lt=deadline)
        for job in jobs:
            job.status = BenchQueue.ABORTED
            job.result_json = '{"reason": "Benchmark timeout"}'
            job.save(using=self._db)

    def is_duplicated(self, team):
        """重複enqueue防止"""
        jobs = self.get_queryset().filter(team=team, status__in=[
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
    STATUS_CHOICES = (
        (WAITING, WAITING), # 処理待ち
        (RUNNING, RUNNING), # 処理中
        (DONE, DONE), # 処理完了
        (ABORTED, ABORTED), # 異常終了
        (CANCELED, CANCELED), # 意図的なキャンセル
    )

    # FIXME: SET_NULLされたレコードを、ジョブ取得時に考慮
    team = models.ForeignKey('authentication.Team', verbose_name="チーム", null=True, on_delete=models.SET_NULL)
    node = models.CharField("ノード", max_length=100)

    # ターゲット情報
    target_hostname = models.CharField("対象ホスト名", max_length=100)
    target_ip = models.CharField("対象IPアドレス", max_length=100)

    # Choice系
    status = models.CharField("進捗", max_length=100, choices=STATUS_CHOICES, default=WAITING)
    is_passed = models.BooleanField("正答フラグ", default=False)

    score = models.IntegerField("獲得スコア", default=0, null=False)

    # ベタテキスト
    result_json = models.TextField("結果JSON")
    log_text = models.TextField("ログ文字列")

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
    def result_json_object(self):
        return json.loads(self.result_json)

    def append_log(self, log):
        self.log_text += log
        self.save(update_fields=["log_raw"])

