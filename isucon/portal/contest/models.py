import datetime
import json

from django.db import models
from django.db.models import Max, Sum

from isucon.portal import settings
from isucon.portal.models import LogicalDeleteMixin
from isucon.portal.contest import exceptions

# FIXME: ベンチマーク対象のサーバを変更する機能
# https://github.com/isucon/isucon8-final/blob/d1480128c917f3fe4d87cb84c83fa2a34ca58d39/portal/lib/ISUCON8/Portal/Web/Controller/API.pm#L32


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


class ServerManager(models.Manager):

    def get_team_servers(self, team):
        """チームが持つサーバ一覧を取得"""
        return self.get_queryset().filter(team=team)


class Server(LogicalDeleteMixin, models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "サーバ"

    # FIXME: パスワード、鍵認証とかにすればいい気がしたのでまだ追加してない

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT)
    hostname = models.CharField("ホスト名", max_length=100, unique=True)

    global_ip = models.CharField("グローバルIPアドレス", max_length=100, unique=True)
    private_ip = models.CharField("プライベートIPアドレス", max_length=100)

    # FIXME: isucon8-finalの時、フィールドとして存在するだけっぽい
    # 使途不明
    private_network = models.CharField("プライベートネットワークアドレス", max_length=100)

    objects = ServerManager()

    def __str__(self):
        return self.hostname


class ScoreHistoryManager(models.Manager):

    def get_queryset_by_team(self, team):
        return self.get_queryset()\
                   .filter(team=team, team__is_active=True, is_passed=True)

    def get_best_score(self, team):
        """指定チームのベストスコアを取得"""
        return self.get_queryset_by_team(team)\
                   .annotate(best_score=Max('score'))[0]

    def get_latest_score(self, team):
        """指定チームの最新スコアを取得"""
        # NOTE: orderingにより最新順に並んでいるので、LIMITで取れば良い
        return self.get_queryset_by_team(team).all()[0]

    def get_top_teams(self, limit=30):
        """トップ30チームの取得"""
        histories = self.get_queryset().filter(team__is_active=True)\
                        .annotate(total_score=Sum('score'))\
                        .order_by('-total_score', '-created_at')[:limit]\
                        .select_related('team', 'team__aggregated_score')

        return [history.team for history in histories]

class ScoreHistory(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "スコア履歴"
        ordering = ('-created_at',)

    team = models.ForeignKey('authentication.Team', verbose_name="チーム", on_delete=models.PROTECT, null=True)
    job = models.ForeignKey('contest.BenchQueue', verbose_name="ベンチキュー", on_delete=models.PROTECT, null=True)
    score = models.IntegerField("得点")
    is_passed = models.BooleanField("正答フラグ", default=False)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("最終更新日時", auto_now=True)

    objects = ScoreHistoryManager()


class BenchQueueManager(models.Manager):

    def get_jobs(self, team):
        return self.get_queryset().filter(team=team)

    def get_recent_jobs(self, team, limit=10):
        """直近10件のジョブを取得"""
        return self.get_queryset().filter(team=team)[:limit]

    def enqueue(self, team):
        # 重複チェック
        if self.is_duplicated(team):
            raise exceptions.DuplicateJobError

        # FIXME: エンキューする際に、リクエスト先サーバを指定できないとダメ
        # isucon8-finalでは、bench_ipがベンチマーク対象のサーバを指しており、
        # private_ipの第４オクテットでそれがベンチマーク対象であるかどうか判断していた様子

        # ベンチマーク対象のサーバを取得
        try:
            server = Server.objects.get(team=team)
        except Server.DoesNotExist:
            raise exceptions.TeamServerDoesNotExistError

        benchmarker = team.benchmarker

        # 追加
        job = self.model(
            team=team,
            target_hostname=server.hostname,
            target_ip=benchmarker.ip,
            node=benchmarker.node,
        )
        job.save(using=self._db)

        return job.id

    def dequeue(self, hostname, max_concurrency=settings.BENCHMARK_MAX_CONCURRENCY):
        # FIXME: 共用ベンチマーカーを用意するならば、ここでtarget_hostnameを指定する必要はなくなる
        job = self.get_queryset().filter(target_hostname=hostname, status=BenchQueue.WAITING).first()
        if job is None:
            raise exceptions.JobDoesNotExistError

        # 状態を処理中にする
        job.status = BenchQueue.RUNNING
        job.save(using=self._db)

        return job

    def abort_timeout(self, timeout_sec=settings.BENCHMARK_ABORT_TIMEOUT_SEC):
        # タイムアウトの締め切り
        deadline = datetime.datetime.now() - datetime.timedelta(seconds=timeout_sec)

        # タイムアウトした(=締め切りより更新時刻が古い) ジョブを aborted にしていく
        jobs = BenchQueue.objects.filter(status=BenchQueue.RUNNING, updated_at__lt=deadline)
        for job in jobs:
            job.abort(result_json='{"reason": "Benchmark timeout"}', log_text='')

    def is_duplicated(self, team):
        """重複enqueue防止"""
        cnt = self.get_queryset().filter(team=team, status__in=[
            BenchQueue.WAITING,
            BenchQueue.RUNNING,
        ]).count()
        return cnt > 0


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

    def done(self, result_json, log_text):
        self.status = BenchQueue.DONE
        self.result_json = result_json
        self.log_text = log_text # FIXME: append? そうなると逐次報告だが、どうログを投げるか話し合う

        # 結果のJSONからスコアや結果を参照し、ジョブに設定
        result_json_object = self.result_json_object
        self.score = result_json_object['score']
        if result_json_object['pass']:
            self.is_passed = True
        self.save()

        ScoreHistory.objects.create(
            team=self.team,
            job=self,
            score=self.score,
            is_passed=self.is_passed,
        )

    def abort(self, result_json, log_text):
        self.status = BenchQueue.ABORTED
        self.result_json = result_json
        self.log_text = log_text
        self.save()

        ScoreHistory.objects.create(
            team=self.team,
            job=self,
            score=0,
            is_passed=self.is_passed,
        )

# FIXME: ランキングを出す際、チームそれぞれのAggregatedScoreが取得されるので結局 N+1 ?
# ベンチ結果次第で、Teamのフィールドとして入れることも考えたほうがいいかもしれない
# AggregatedScoreは、Django signals を用いることで、チーム登録時に作成され、得点履歴が追加されるごとに更新されます
class AggregatedScore(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "集計スコア"

    total_score = models.IntegerField('合計スコア', default=0)
    best_score = models.IntegerField('ベストスコア', default=0)
    latest_score = models.IntegerField('最新獲得スコア', default=0)
    # latest_status = is_passed (True | False)
    # FIXME: is_passedではなく、BenchQueue.statusと勘違いしうるため、名前改善したほうが良さそう
    latest_status = models.BooleanField('最新ベンチステータス', default=False)